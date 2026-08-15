import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";
import { BACKEND_BASE_URL } from "@config/env";

export type IntakeSessionQuestion = {
  key: string;
  title: string;
  text: string;
  type: string;
  options?:
    | Array<{
        label: string;
        value: string;
        hint?: string;
      }>
    | Record<string, string>;
};

export type IntakeSessionCreateMode = "guided" | "llm";

export type CreateGuidedIntakeSessionResponse = {
  mode: "guided";
  session_id: string;
  status: string;
  current_index: number;
  total_questions?: number;
  first_question?: IntakeSessionQuestion | null;
};

export type SubmitIntakeSessionAnswerBody = {
  key: string;
  answers:
    | string
    | string[]
    | { min: number | null; max: number | null }
    | { city?: string; state?: string; country?: string; label?: string; input?: string };
};

export type SubmitIntakeSessionAnswerResponse = {
  session: {
    id?: string;
    status?: string;
    criteria?: Record<string, unknown> | null;
  };
  next_question: IntakeSessionQuestion | null;
};

export type CompleteIntakeSessionResponse = {
  id?: string;
  status?: string;
  created_at?: string;
  search_profile_id?: string | null;
  criteria?: Record<string, unknown> | null;
};

export type GetIntakeSessionResponse = {
  id?: string | null;
  status?: string;
  criteria?: Record<string, unknown> | null;
  current_index?: number;
  total_questions?: number;
  question_history?: IntakeSessionQuestion[];
  next_question?: IntakeSessionQuestion | null;
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

export type CreateLlmIntakeSessionResponse = {
  mode: "llm";
  session_id: string;
  status: string;
  current_index: number;
  total_questions: number;
  message: string;
  next_question: LlmNextQuestion | null;
};

export type LlmInputResponse = {
  mode: "llm";
  extracted: LlmExtracted;
  criteria: Record<string, unknown>;
  current_index: number;
  total_questions: number;
  missing_fields: string[];
  skipped_fields: string[];
  question_titles: Record<string, string>;
  next_question: LlmNextQuestion | null;
  is_complete: boolean;
};

export type LlmInputBody = {
  input: string;
  mode: "llm";
};

export type IntakeJobStatus = "queued" | "running" | "succeeded" | "failed";

export const TERMINAL_JOB_STATUSES: readonly IntakeJobStatus[] = ["succeeded", "failed"];

/** `202` body: the turn was accepted, not run. Follow the job for the result. */
export type EnqueuedLlmJob = {
  job_id: string;
  status: IntakeJobStatus;
};

export type IntakeJobState = {
  job_id: string;
  status: IntakeJobStatus;
  result: LlmInputResponse | null;
  error: string | null;
};

export type JobSubscription = {
  /** Every state the job passes through, including the first frame on connect. */
  onUpdate?: (state: IntakeJobState) => void;
  onSettled: (state: IntakeJobState) => void;
  /** The stream died or timed out — the caller should fall back to polling. */
  onStreamLost: () => void;
};

export const intakeJobStreamUrl = (sessionId: string, jobId: string): string =>
  `${BACKEND_BASE_URL}/api/v1/intake-sessions/${sessionId}/jobs/${jobId}/stream`;

/**
 * Follow a job over SSE. Returns an unsubscribe function.
 *
 * These routes are anonymous, which is what makes `EventSource` usable at all — it
 * cannot send an Authorization header, so a bearer-token endpoint would need a polling
 * client instead.
 */
export const subscribeToJob = (
  sessionId: string,
  jobId: string,
  handlers: JobSubscription,
): (() => void) => {
  if (typeof EventSource === "undefined") {
    // Server-side render, or a test environment without the API. Polling covers it.
    handlers.onStreamLost();
    return () => {};
  }

  const source = new EventSource(intakeJobStreamUrl(sessionId, jobId));
  let closed = false;
  const close = () => {
    if (closed) return;
    closed = true;
    source.close();
  };

  source.onmessage = (event: MessageEvent<string>) => {
    let state: IntakeJobState;
    try {
      state = JSON.parse(event.data) as IntakeJobState;
    } catch {
      return;
    }
    handlers.onUpdate?.(state);
    if (TERMINAL_JOB_STATUSES.includes(state.status)) {
      close();
      handlers.onSettled(state);
    }
  };

  // The server sends this when it stops watching a job that is still running: the turn
  // may yet finish, so it means "keep looking elsewhere", not "this failed".
  source.addEventListener("timeout", () => {
    close();
    handlers.onStreamLost();
  });

  source.onerror = () => {
    close();
    handlers.onStreamLost();
  };

  return close;
};

export class IntakeSessionsService {
  constructor(private readonly http: AxiosInstance) {}

  async createSession(mode: "guided"): Promise<CreateGuidedIntakeSessionResponse>;
  async createSession(mode: "llm"): Promise<CreateLlmIntakeSessionResponse>;
  async createSession(
    mode: IntakeSessionCreateMode,
  ): Promise<CreateGuidedIntakeSessionResponse | CreateLlmIntakeSessionResponse> {
    const { data } = await this.http.post<
      CreateGuidedIntakeSessionResponse | CreateLlmIntakeSessionResponse
    >("/intake-sessions", undefined, { params: { mode } });
    return data;
  }

  async getSession(sessionId: string): Promise<GetIntakeSessionResponse> {
    const { data } = await this.http.get<GetIntakeSessionResponse>(
      `/intake-sessions/${sessionId}`,
    );
    return data;
  }

  async submitAnswer(
    sessionId: string,
    body: SubmitIntakeSessionAnswerBody,
  ): Promise<SubmitIntakeSessionAnswerResponse> {
    const { data } = await this.http.patch<SubmitIntakeSessionAnswerResponse>(
      `/intake-sessions/${sessionId}/answers/guided`,
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

  /**
   * Hand the turn to the backend and get a job back.
   *
   * The result no longer arrives here: a provider stall used to surface as a 5xx that
   * took the user's message with it, so the text is made durable first and delivered
   * through the job.
   */
  async enqueueLlmInput(
    sessionId: string,
    body: LlmInputBody,
  ): Promise<EnqueuedLlmJob> {
    const { data } = await this.http.post<EnqueuedLlmJob>(
      `/intake-sessions/${sessionId}/answers/llm`,
      body,
    );
    return data;
  }

  async getLlmJob(sessionId: string, jobId: string): Promise<IntakeJobState> {
    const { data } = await this.http.get<IntakeJobState>(
      `/intake-sessions/${sessionId}/jobs/${jobId}`,
    );
    return data;
  }
}

export const intakeSessionsService = new IntakeSessionsService(apiClient);
