"use client";

import type { RefObject } from "react";
import { Send } from "lucide-react";

import { styles } from "../styles";

type ChatComposerProps = {
  draft: string;
  setDraft: (value: string) => void;
  textareaRef: RefObject<HTMLTextAreaElement | null>;
  sessionId: string | null;
  isSending: boolean;
  onSend: () => void;
};

export const ChatComposer = ({
  draft,
  setDraft,
  textareaRef,
  sessionId,
  isSending,
  onSend,
}: ChatComposerProps) => (
  <div className={styles.composer}>
    <div className={styles.composerInner}>
      <textarea
        ref={textareaRef}
        className={styles.textarea}
        placeholder="Type your requirements..."
        value={draft}
        disabled={!sessionId || isSending}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend();
          }
        }}
        rows={3}
      />
      <button
        type="button"
        className={styles.sendButton}
        aria-label="Send message"
        disabled={!sessionId || !draft.trim() || isSending}
        onClick={() => onSend()}
      >
        <Send className="size-4" aria-hidden />
      </button>
    </div>
  </div>
);
