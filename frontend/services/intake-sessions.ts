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

/** Query param for ``POST /intake-sessions`` (default on API is ``guided``). */
export type IntakeSessionCreateMode = "guided" | "llm";

export type CreateIntakeSessionResponse = {
  session_id: string;
  status: string;
  /** Present when the API returns questionnaire length; otherwise treat as single-step. */
  total_questions?: number;
  /** Set for ``guided`` mode; may be absent for ``llm`` (welcome-only) responses. */
  first_question?: IntakeSessionQuestion | null;
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

export type LlmExtractedLocation = {
  label: string;
  lat: number;
  lng: number;
};

export type LlmExtractedRange = {
  min: number;
  max: number;
};

export type LlmExtracted = {
  building_type: string[];
  location: LlmExtractedLocation | null;
  size_sqft: LlmExtractedRange;
  rent_range: LlmExtractedRange;
};

export type LlmNextQuestion = {
  key: string;
  text: string;
  type: string;
  options?: unknown;
};

export type LlmInputResponse = {
  mode: "llm";
  extracted: LlmExtracted;
  criteria: Record<string, unknown>;
  current_index: number;
  total_questions: number;
  missing_fields: string[];
  next_question: LlmNextQuestion | null;
  is_complete: boolean;
};

export type LlmInputBody = {
  input: string;
  mode: "llm";
};

export class IntakeSessionsService {
  constructor(private readonly http: AxiosInstance) {}

  async createSession(
    mode: IntakeSessionCreateMode,
  ): Promise<CreateIntakeSessionResponse> {
    const { data } = await this.http.post<CreateIntakeSessionResponse>(
      "/intake-sessions",
      undefined,
      { params: { mode } },
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

  async submitLlmInput(
    sessionId: string,
    body: LlmInputBody,
  ): Promise<LlmInputResponse> {
    const { data } = await this.http.post<LlmInputResponse>(
      `/intake-sessions/${sessionId}/llm-input`,
      body,
    );
    return data;
  }
}

export const intakeSessionsService = new IntakeSessionsService(apiClient);
