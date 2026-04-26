import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";

export type IntakeSessionQuestion = {
  key: string;
  text: string;
  type: string;
  options?: Array<{
    label: string;
    value: string;
    hint?: string;
  }>;
};

export type CreateIntakeSessionResponse = {
  session_id: string;
  status: string;
  total_questions: number;
  first_question: IntakeSessionQuestion;
};

export type SubmitIntakeSessionAnswerBody = {
  key: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  answers: any;
};

export type SubmitIntakeSessionAnswerResponse = {
  session: {
    id?: string;
    status?: string;
    criteria?: Record<string, unknown> | null;
  };
  next_question: IntakeSessionQuestion | null;
};

/** Response from `POST /intake-sessions/{session_id}/complete` (matches backend `IntakeSession`). */
export type CompleteIntakeSessionResponse = {
  id?: string;
  status?: string;
  criteria?: Record<string, unknown> | null;
};

export class IntakeSessionsService {
  constructor(private readonly http: AxiosInstance) {}

  async createSession(): Promise<CreateIntakeSessionResponse> {
    const { data } = await this.http.post<CreateIntakeSessionResponse>(
      "/intake-sessions",
    );
    return data;
  }

  async submitAnswer(
    sessionId: string,
    body: SubmitIntakeSessionAnswerBody,
  ): Promise<SubmitIntakeSessionAnswerResponse> {
    const { data } = await this.http.patch<SubmitIntakeSessionAnswerResponse>(
      `/intake-sessions/${sessionId}/answers`,
      body,
    );
    return data;
  }

  async completeSession(
    sessionId: string,
  ): Promise<CompleteIntakeSessionResponse> {
    const { data } = await this.http.post<CompleteIntakeSessionResponse>(
      `/intake-sessions/${sessionId}/complete`,
    );
    return data;
  }
}

export const intakeSessionsService = new IntakeSessionsService(apiClient);
