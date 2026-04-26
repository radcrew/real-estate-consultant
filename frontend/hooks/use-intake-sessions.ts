"use client";

import { useCallback } from "react";

import {
  intakeSessionsService,
  type LlmInputBody,
  type LlmInputResponse,
  type SubmitIntakeSessionAnswerBody,
  type SubmitIntakeSessionAnswerResponse,
  type CreateIntakeSessionResponse,
  type CompleteIntakeSessionResponse,
} from "@services/intake-sessions";

export const useIntakeSessions = () => {
  const createSession = useCallback((): Promise<CreateIntakeSessionResponse> => {
    return intakeSessionsService.createSession();
  }, []);

  const submitAnswer = useCallback(
    (
      sessionId: string,
      body: SubmitIntakeSessionAnswerBody,
    ): Promise<SubmitIntakeSessionAnswerResponse> => {
      return intakeSessionsService.submitAnswer(sessionId, body);
    },
    [],
  );

  const completeSession = useCallback(
    (sessionId: string): Promise<CompleteIntakeSessionResponse> => {
      return intakeSessionsService.completeSession(sessionId);
    },
    [],
  );

  const submitLlmInput = useCallback(
    (sessionId: string, body: LlmInputBody): Promise<LlmInputResponse> => {
      return intakeSessionsService.submitLlmInput(sessionId, body);
    },
    [],
  );

  return {
    createSession,
    submitAnswer,
    completeSession,
    submitLlmInput,
  };
};
