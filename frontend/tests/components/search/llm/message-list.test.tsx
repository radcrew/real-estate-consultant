// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MessageList } from "@components/search/wizard/modes/llm/panels/chat/message-list";
import type { ChatMessage } from "@components/search/wizard/modes/llm/types";

const MESSAGES: ChatMessage[] = [
  { id: "1", role: "user", content: "I need a warehouse in Austin." },
  { id: "2", role: "assistant", content: "Got it! What size do you need?" },
];

describe("MessageList", () => {
  it("renders user messages", () => {
    render(<MessageList messages={MESSAGES} isSending={false} />);
    expect(screen.getByText("I need a warehouse in Austin.")).toBeInTheDocument();
  });

  it("renders assistant messages", () => {
    render(<MessageList messages={MESSAGES} isSending={false} />);
    expect(screen.getByText("Got it! What size do you need?")).toBeInTheDocument();
  });

  it("shows thinking indicator while sending", () => {
    render(<MessageList messages={[]} isSending={true} />);
    expect(screen.getByText(/thinking/i)).toBeInTheDocument();
  });

  it("renders no message bubbles when messages is empty and not sending", () => {
    render(<MessageList messages={[]} isSending={false} />);
    expect(screen.queryByText(/thinking/i)).not.toBeInTheDocument();
  });
});
