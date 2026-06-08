"use client";

import { intakeSessionsService } from "@services/intake-sessions";

// Bind once so callers get stable references (and `createSession` keeps its
// overload signatures) that are safe to list in effect/callback deps.
const createSession = intakeSessionsService.createSession.bind(intakeSessionsService);
const getSession = intakeSessionsService.getSession.bind(intakeSessionsService);
const submitAnswer = intakeSessionsService.submitAnswer.bind(intakeSessionsService);
const completeSession = intakeSessionsService.completeSession.bind(intakeSessionsService);
const submitLlmInput = intakeSessionsService.submitLlmInput.bind(intakeSessionsService);

export const useIntakeSessions = () => ({
  createSession,
  getSession,
  submitAnswer,
  completeSession,
  submitLlmInput,
});
