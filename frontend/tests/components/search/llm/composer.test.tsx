// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatComposer } from "@components/search/wizard/modes/llm/panels/chat/composer";

describe("ChatComposer", () => {
  const baseProps = {
    draft: "",
    setDraft: vi.fn(),
    textareaRef: { current: null },
    sessionId: "sess-1",
    isSending: false,
    onSend: vi.fn(),
  };

  it("renders the textarea", () => {
    render(<ChatComposer {...baseProps} />);
    expect(screen.getByPlaceholderText(/type your requirements/i)).toBeInTheDocument();
  });

  it("disables textarea when sessionId is null", () => {
    render(<ChatComposer {...baseProps} sessionId={null} />);
    expect(screen.getByPlaceholderText(/type your requirements/i)).toBeDisabled();
  });

  it("disables send button when draft is empty", () => {
    render(<ChatComposer {...baseProps} draft="" />);
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });

  it("calls onSend when send button clicked", () => {
    const onSend = vi.fn();
    render(<ChatComposer {...baseProps} draft="Hello" onSend={onSend} />);
    fireEvent.click(screen.getByRole("button", { name: /send/i }));
    expect(onSend).toHaveBeenCalledTimes(1);
  });

  it("calls onSend when Enter is pressed (no shift)", () => {
    const onSend = vi.fn();
    render(<ChatComposer {...baseProps} draft="Hello" onSend={onSend} />);
    fireEvent.keyDown(screen.getByPlaceholderText(/type your requirements/i), { key: "Enter", shiftKey: false });
    expect(onSend).toHaveBeenCalledTimes(1);
  });

  it("does not call onSend when Shift+Enter is pressed", () => {
    const onSend = vi.fn();
    render(<ChatComposer {...baseProps} draft="Hello" onSend={onSend} />);
    fireEvent.keyDown(screen.getByPlaceholderText(/type your requirements/i), { key: "Enter", shiftKey: true });
    expect(onSend).not.toHaveBeenCalled();
  });
});
