// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { ChatPanel } from "@components/search/wizard/modes/llm/panels/chat";

const mockWizard = vi.fn();
vi.mock("@contexts/search-wizard", () => ({
  useSearchWizard: () => mockWizard(),
}));

const mockRunTurn = vi.fn();
vi.mock("@hooks/use-intake-job", () => ({
  useIntakeJob: () => ({ runTurn: (...a: unknown[]) => mockRunTurn(...a), isRunning: false }),
}));
vi.mock("@services/intake-sessions", () => ({}));

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

  it("sends a message and calls onLlmSuccess on reply", async () => {
    mockRunTurn.mockResolvedValue({
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

  it("keeps the typed message visible while the turn is still running", async () => {
    let settle: (value: unknown) => void = () => {};
    mockRunTurn.mockReturnValue(new Promise((resolve) => { settle = resolve; }));
    render(<ChatPanel onLlmSuccess={vi.fn()} />);
    fireEvent.change(screen.getByPlaceholderText(/type your requirements/i), {
      target: { value: "Warehouse in Austin" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));

    // The turn is durable server-side, so the message stays put rather than waiting on
    // a reply that may take a while.
    expect(await screen.findByText("Warehouse in Austin")).toBeInTheDocument();
    settle({ criteria: {}, missing_fields: [], question_titles: {}, next_question: null });
  });

  it("surfaces the job's own failure reason and restores the draft", async () => {
    const setErrorMessage = vi.fn();
    mockWizard.mockReturnValue({
      sessionId: "sess-1", errorMessage: null,
      isLoadingQuestion: false, isSubmitting: false,
      llmChatBootstrap: null, setErrorMessage, clearLlmChatBootstrap: vi.fn(),
    });
    mockRunTurn.mockRejectedValue(new Error("The assistant's reply didn't come through."));
    render(<ChatPanel onLlmSuccess={vi.fn()} />);
    const textarea = screen.getByPlaceholderText(/type your requirements/i);
    fireEvent.change(textarea, { target: { value: "Warehouse in Austin" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() =>
      expect(setErrorMessage).toHaveBeenCalledWith(
        "The assistant's reply didn't come through.",
      ),
    );
    // Rolled back, so the user can retry without retyping.
    await waitFor(() => expect(textarea).toHaveValue("Warehouse in Austin"));
  });
});
