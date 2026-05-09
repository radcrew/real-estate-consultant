"use client";

import { Bot, Loader2, UserRound } from "lucide-react";

import { STYLES } from "../../styles";
import type { ChatMessage } from "../../types";

type MessageListProps = {
  messages: ChatMessage[];
  isSending: boolean;
};

export const MessageList = ({ messages, isSending }: MessageListProps) => (
  <div className={STYLES.messages}>
    {messages.map((msg) =>
      msg.role === "user" ? (
        <div key={msg.id} className={STYLES.messageRowUser}>
          <div className={STYLES.bubbleUser}>{msg.content}</div>
          <div className={STYLES.avatarUser} aria-hidden>
            <UserRound className="size-4" />
          </div>
        </div>
      ) : (
        <div key={msg.id} className={STYLES.messageRowBot}>
          <div className={STYLES.avatarBot} aria-hidden>
            <Bot className="size-4" />
          </div>
          <div className={STYLES.bubbleBot}>{msg.content}</div>
        </div>
      ),
    )}
    {isSending && (
      <div className={STYLES.messageRowBot}>
        <div className={STYLES.avatarBot} aria-hidden>
          <Bot className="size-4" />
        </div>
        <div className={STYLES.typingBubble}>
          <Loader2 className="size-4 animate-spin" aria-hidden />
          Thinking…
        </div>
      </div>
    )}
  </div>
);
