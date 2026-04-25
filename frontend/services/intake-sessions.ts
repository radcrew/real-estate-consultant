import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";

export type IntakeSessionQuestion = {
  key: string;
  text: string;
  type: string;
};

export type CreateIntakeSessionResponse = {
  session_id: string;
  status: string;
  first_question: IntakeSessionQuestion;
};

export type SubmitIntakeSessionAnswerBody = {
  key: string;
  answers: string | string[] | number;
};

export type SubmitIntakeSessionAnswerResponse = {
  session: {
    id?: string;
    status?: string;
    criteria?: Record<string, unknown> | null;
  };
  next_question: IntakeSessionQuestion | null;
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
}

export const intakeSessionsService = new IntakeSessionsService(apiClient);
