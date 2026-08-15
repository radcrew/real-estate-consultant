"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { isAxiosError } from "axios";

import {
  TERMINAL_JOB_STATUSES,
  intakeSessionsService,
  subscribeToJob,
  type IntakeJobState,
  type LlmInputResponse,
} from "@services/intake-sessions";

/** Matches the server's stream deadline, so polling outlives a dropped connection. */
const JOB_DEADLINE_MS = 600_000;
const POLL_INTERVAL_MS = 1_000;

const GENERIC_FAILURE = "That message couldn't be processed. Please try again.";

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
 * The turn is accepted durably, then followed: SSE while the connection holds, polling
 * when it does not. Polling is the fallback rather than the primary channel because a
 * dropped `EventSource` with nothing behind it strands a turn the backend has already
 * paid a model to run.
 */
export const useIntakeJob = (): UseIntakeJobResult => {
  const [isRunning, setRunning] = useState(false);
  const cleanupRef = useRef<(() => void) | null>(null);
  const abandonedRef = useRef(false);

  useEffect(() => {
    return () => {
      abandonedRef.current = true;
      cleanupRef.current?.();
    };
  }, []);

  const pollUntilSettled = useCallback(
    async (sessionId: string, jobId: string, deadline: number): Promise<IntakeJobState> => {
      for (;;) {
        try {
          const state = await intakeSessionsService.getLlmJob(sessionId, jobId);
          if (isTerminal(state) || Date.now() >= deadline) return state;
        } catch (e) {
          // This path is reached *because* the stream already failed, so the connection
          // is known to be unreliable — treating one bad response as a dead turn would
          // discard a message the server is very likely still processing.
          // A 404 is the exception: the job does not exist, and asking again will not
          // change that.
          if (isAxiosError(e) && e.response?.status === 404) throw e;
          if (Date.now() >= deadline) throw e;
        }
        await sleep(POLL_INTERVAL_MS);
      }
    },
    [],
  );

  const followJob = useCallback(
    (sessionId: string, jobId: string, deadline: number): Promise<IntakeJobState> =>
      new Promise<IntakeJobState>((resolve, reject) => {
        const unsubscribe = subscribeToJob(sessionId, jobId, {
          onSettled: (state) => {
            cleanupRef.current = null;
            resolve(state);
          },
          onStreamLost: () => {
            cleanupRef.current = null;
            // Not a failure: the job is very likely still running. Keep asking.
            pollUntilSettled(sessionId, jobId, deadline).then(resolve, reject);
          },
        });
        cleanupRef.current = unsubscribe;
      }),
    [pollUntilSettled],
  );

  const runTurn = useCallback(
    async (sessionId: string, input: string): Promise<LlmInputResponse> => {
      setRunning(true);
      try {
        const enqueued = await intakeSessionsService.enqueueLlmInput(sessionId, {
          input,
          mode: "llm",
        });

        const deadline = Date.now() + JOB_DEADLINE_MS;
        // Deployments without a queue run the turn inside the request and hand back a
        // finished job, so opening a stream for it would only add a round trip.
        const settled = TERMINAL_JOB_STATUSES.includes(enqueued.status)
          ? await intakeSessionsService.getLlmJob(sessionId, enqueued.job_id)
          : await followJob(sessionId, enqueued.job_id, deadline);

        if (settled.status !== "succeeded" || !settled.result) {
          throw new Error(settled.error ?? GENERIC_FAILURE);
        }
        return settled.result;
      } finally {
        if (!abandonedRef.current) setRunning(false);
      }
    },
    [followJob],
  );

  return { runTurn, isRunning };
};
