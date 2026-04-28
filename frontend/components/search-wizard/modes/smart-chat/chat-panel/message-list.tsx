"use client";

import { Bot, Loader2, UserRound } from "lucide-react";

import { styles } from "../styles";
import type { ChatMessage } from "../types";

type MessageListProps = {
  messages: ChatMessage[];
  isSending: boolean;
};

export const MessageList = ({ messages, isSending }: MessageListProps) => (
  <div className={styles.messages}>
    {messages.map((msg) =>
      msg.role === "user" ? (
        <div key={msg.id} className={styles.messageRowUser}>
          <div className={styles.bubbleUser}>{msg.content}</div>
          <div className={styles.avatarUser} aria-hidden>
            <UserRound className="size-4" />
          </div>
        </div>
      ) : (
        <div key={msg.id} className={styles.messageRowBot}>
          <div className={styles.avatarBot} aria-hidden>
            <Bot className="size-4" />
          </div>
          <div className={styles.bubbleBot}>{msg.content}</div>
        </div>
      ),
    )}
    {isSending && (
      <div className={styles.messageRowBot}>
        <div className={styles.avatarBot} aria-hidden>
          <Bot className="size-4" />
        </div>
        <div className={styles.typingBubble}>
          <Loader2 className="size-4 animate-spin" aria-hidden />
          Thinking…
        </div>
      </div>
    )}
  </div>
);
