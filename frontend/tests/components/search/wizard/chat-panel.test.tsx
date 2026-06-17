// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { ChatPanel } from "@components/search/wizard/modes/llm/panels/chat";

const mockWizard = vi.fn();
vi.mock("@contexts/search-wizard", () => ({
  useSearchWizard: () => mockWizard(),
}));

const mockSubmitLlm = vi.fn();
vi.mock("@services/intake-sessions", () => ({
  intakeSessionsService: { submitLlmInput: (...a: unknown[]) => mockSubmitLlm(...a) },
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockWizard.mockReturnValue({
    sessionId: "sess-1",
    errorMessage: null,
    isLoadingQuestion: false,
    isSubmitting: false,
    llmChatBootstrap: null,
    setErrorMessage: vi.fn(),
    clearLlmChatBootstrap: vi.fn(),
  });
});

describe("ChatPanel", () => {
  it("renders the AI Property Assistant heading", () => {
    render(<ChatPanel onLlmSuccess={vi.fn()} />);
    expect(screen.getByText(/AI Property Assistant/i)).toBeInTheDocument();
  });

  it("renders the textarea composer", () => {
    render(<ChatPanel onLlmSuccess={vi.fn()} />);
    expect(screen.getByPlaceholderText(/type your requirements/i)).toBeInTheDocument();
  });

  it("shows connecting when busy loading and no session yet", () => {
    mockWizard.mockReturnValue({
      sessionId: null, errorMessage: null,
      isLoadingQuestion: true, isSubmitting: false,
      llmChatBootstrap: null, setErrorMessage: vi.fn(), clearLlmChatBootstrap: vi.fn(),
    });
    render(<ChatPanel onLlmSuccess={vi.fn()} />);
    expect(screen.getByText(/connecting/i)).toBeInTheDocument();
  });

  it("shows error banner when errorMessage is set", () => {
    mockWizard.mockReturnValue({
      sessionId: "s1", errorMessage: "Something went wrong",
      isLoadingQuestion: false, isSubmitting: false,
      llmChatBootstrap: null, setErrorMessage: vi.fn(), clearLlmChatBootstrap: vi.fn(),
    });
    render(<ChatPanel onLlmSuccess={vi.fn()} />);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("sends a message and calls onLlmSuccess on reply", async () => {
    mockSubmitLlm.mockResolvedValue({
      criteria: { location: "Austin" }, missing_fields: [], question_titles: {},
      next_question: { text: "What size do you need?" },
    });
    const onLlmSuccess = vi.fn();
    render(<ChatPanel onLlmSuccess={onLlmSuccess} />);
    const textarea = screen.getByPlaceholderText(/type your requirements/i);
    fireEvent.change(textarea, { target: { value: "Warehouse in Austin" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => expect(onLlmSuccess).toHaveBeenCalledTimes(1));
    expect(screen.getByText("What size do you need?")).toBeInTheDocument();
  });
});
