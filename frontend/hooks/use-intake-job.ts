"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { isAxiosError } from "axios";

import {
  TERMINAL_JOB_STATUSES,
  intakeSessionsService,
  type IntakeJobState,
  type LlmInputResponse,
} from "@services/intake-sessions";

/**
 * How long to follow a turn before giving up.
 *
 * Keep in step with the backend's `CHAT_JOB_ABANDONED_AFTER_SECONDS`, which is when it
 * releases the session's in-flight slot. Give up sooner and the user is told their turn
 * failed while the next attempt is still refused as "still working".
 */
const JOB_DEADLINE_MS = 600_000;
const POLL_INTERVAL_MS = 1_000;

const GENERIC_FAILURE = "That message couldn't be processed. Please try again.";
/** Rejection reason when the caller is gone; nothing is listening by then. */
const ABANDONED = "Intake job no longer being followed.";

/**
 * How many polls in a row may fail before giving up.
 *
 * Tolerating a blip is worth it; tolerating everything is not. Retrying a persistent
 * fault to the deadline makes a broken turn indistinguishable from a slow one — the user
 * watches "thinking" for ten minutes and no error ever reaches them.
 */
const MAX_CONSECUTIVE_POLL_FAILURES = 3;

/** A client error will not fix itself, so retrying only delays telling the user. */
const isPermanent = (status: number | undefined): boolean =>
  status !== undefined && status >= 400 && status < 500 && status !== 408 && status !== 429;

const isTerminal = (state: IntakeJobState): boolean =>
  TERMINAL_JOB_STATUSES.includes(state.status);

const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

type UseIntakeJobResult = {
  runTurn: (sessionId: string, input: string) => Promise<LlmInputResponse>;
  isRunning: boolean;
};

/**
 * Submit one intake turn and resolve with its result.
 *
 * The turn is accepted durably and then polled. Streaming was tried and removed: these
 * routes require a bearer token, and `EventSource` cannot send one — see
 * `services/intake-sessions.ts`. Polling also keeps no serverless function held open per
 * waiting client.
 */
export const useIntakeJob = (): UseIntakeJobResult => {
  const [isRunning, setRunning] = useState(false);
  const abandonedRef = useRef(false);

  useEffect(() => {
    // Set on mount, not just cleared on unmount. StrictMode runs effects twice in
    // development — mount, unmount, remount — so a flag only ever set to true on cleanup
    // stays true after the simulated unmount, and every turn then aborts on its first
    // poll. Production mounts once and never notices.
    abandonedRef.current = false;
    return () => {
      abandonedRef.current = true;
    };
  }, []);

  const pollUntilSettled = useCallback(
    async (sessionId: string, jobId: string, deadline: number): Promise<IntakeJobState> => {
      let consecutiveFailures = 0;
      for (;;) {
        // Nothing else can stop this loop, so a component that has gone away has to be
        // noticed here — otherwise it keeps calling the API until the deadline.
        if (abandonedRef.current) throw new Error(ABANDONED);
        try {
          const state = await intakeSessionsService.getLlmJob(sessionId, jobId);
          consecutiveFailures = 0;
          if (isTerminal(state) || Date.now() >= deadline) return state;
        } catch (e) {
          // One bad response is not a dead turn — the server is very likely still
          // processing it. But a 401, 403 or 404 is an answer, not a blip, and a fault
          // that repeats is not going to stop repeating.
          if (isAxiosError(e) && isPermanent(e.response?.status)) throw e;
          consecutiveFailures += 1;
          if (consecutiveFailures >= MAX_CONSECUTIVE_POLL_FAILURES) throw e;
          if (Date.now() >= deadline) throw e;
        }
        await sleep(POLL_INTERVAL_MS);
      }
    },
    [],
  );

  const runTurn = useCallback(
    async (sessionId: string, input: string): Promise<LlmInputResponse> => {
      setRunning(true);
      try {
        const enqueued = await intakeSessionsService.enqueueLlmInput(sessionId, {
          input,
          mode: "llm",
        });

        // Deployments without a queue run the turn inside the request and hand back a
        // finished job, so there is nothing left to wait for.
        const settled = TERMINAL_JOB_STATUSES.includes(enqueued.status)
          ? await intakeSessionsService.getLlmJob(sessionId, enqueued.job_id)
          : await pollUntilSettled(sessionId, enqueued.job_id, Date.now() + JOB_DEADLINE_MS);

        if (settled.status !== "succeeded" || !settled.result) {
          throw new Error(settled.error ?? GENERIC_FAILURE);
        }
        return settled.result;
      } finally {
        if (!abandonedRef.current) setRunning(false);
      }
    },
    [pollUntilSettled],
  );

  return { runTurn, isRunning };
};
