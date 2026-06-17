// @vitest-environment jsdom
import { render, screen, act } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SmartChat } from "@components/search/wizard/modes/llm";

vi.mock("@components/search/wizard/modes/llm/panels/chat", () => ({
  ChatPanel: ({ onLlmSuccess }: { onLlmSuccess: (d: unknown) => void }) => (
    <div data-testid="chat-panel">
      <button onClick={() => onLlmSuccess({ criteria: { location: "Austin" }, missing_fields: [], question_titles: {} })}>
        send
      </button>
    </div>
  ),
}));

vi.mock("@components/search/wizard/modes/llm/panels/side", () => ({
  SidePanel: ({ lastResponse }: { lastResponse: unknown }) => (
    <div data-testid="side-panel" data-has-response={lastResponse != null ? "true" : "false"} />
  ),
}));

describe("SmartChat", () => {
  it("renders the chat panel", () => {
    render(<SmartChat />);
    expect(screen.getByTestId("chat-panel")).toBeInTheDocument();
  });

  it("renders the side panel", () => {
    render(<SmartChat />);
    expect(screen.getByTestId("side-panel")).toBeInTheDocument();
  });

  it("passes llm response from chat panel to side panel", async () => {
    const { getByRole, getByTestId } = render(<SmartChat />);
    expect(getByTestId("side-panel").dataset.hasResponse).toBe("false");
    await act(async () => { getByRole("button", { name: "send" }).click(); });
    expect(getByTestId("side-panel").dataset.hasResponse).toBe("true");
  });
});
