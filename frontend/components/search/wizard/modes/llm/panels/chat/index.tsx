"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { isAxiosError } from "axios";
import { Bot, Loader2 } from "lucide-react";

import { useSearchWizard } from "@contexts/search-wizard";
import { useIntakeJob } from "@hooks/use-intake-job";
import { getApiErrorMessage } from "@utils/common";
import { type LlmInputResponse } from "@services/intake-sessions";

import type { ChatMessage } from "../../types";
import { ChatComposer } from "./composer";
import { MessageList } from "./message-list";
import { STYLES } from "../../styles";

type ChatPanelProps = {
  onLlmSuccess: (data: LlmInputResponse) => void;
};

// A failed job rejects with the reason the backend recorded, which is more specific than
// anything derived from the HTTP call that merely accepted the turn.
const describeError = (e: unknown): string => {
  if (isAxiosError(e)) return getApiErrorMessage(e);
  if (e instanceof Error && e.message) return e.message;
  return getApiErrorMessage(e);
};

export const ChatPanel = ({ onLlmSuccess }: ChatPanelProps) => {
  const {
    clearLlmChatBootstrap,
    isLoadingQuestion,
    isSubmitting,
    llmChatBootstrap,
    sessionId,
    setErrorMessage,
  } = useSearchWizard();

  const { runTurn } = useIntakeJob();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const bootstrapAppliedForSession = useRef<string | null>(null);

  const isBusy = isLoadingQuestion && !sessionId;

  useEffect(() => {
    if (!sessionId) {
      bootstrapAppliedForSession.current = null;
      return;
    }

    if (
      !llmChatBootstrap?.length ||
      bootstrapAppliedForSession.current === sessionId
    ) {
      return;
    }

    bootstrapAppliedForSession.current = sessionId;
    setMessages(
      llmChatBootstrap.map((content) => ({
        id: crypto.randomUUID(),
        role: "assistant" as const,
        content,
      })),
    );
    clearLlmChatBootstrap();
  }, [sessionId, llmChatBootstrap, clearLlmChatBootstrap]);

  useEffect(() => {
    textareaRef.current?.focus();
  }, [sessionId, messages.length]);

  const handleSend = useCallback(async () => {
    const text = draft.trim();
    if (!sessionId || !text || isSending || isSubmitting) {
      return;
    }

    setSending(true);
    setErrorMessage(null);
    setDraft("");

    // Shown immediately and held until the job resolves — the turn is durable on the
    // server before any model runs, so the message is not lost if the reply is slow.
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };
    setMessages((m) => [...m, userMsg]);

    try {
      const data = await runTurn(sessionId, text);
      onLlmSuccess(data);

      const followUp = data.next_question?.text?.trim();
      const assistantReply =
        followUp ||
        (data.missing_fields.length === 0
          ? "You're all set! You can start searching properties now, or tell me if you'd like to update anything."
          : "");

      if (assistantReply) {
        setMessages((m) => [
          ...m,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: assistantReply,
          },
        ]);
      }
    } catch (err) {
      setErrorMessage(describeError(err));
      setMessages((m) => m.filter((x) => x.id !== userMsg.id));
      setDraft(text);
    } finally {
      setSending(false);
    }
  }, [
    draft,
    isSending,
    isSubmitting,
    onLlmSuccess,
    runTurn,
    sessionId,
    setErrorMessage,
  ]);

  return (
    <div className={STYLES.chatColumn}>
      <header className={STYLES.chatHeader}>
        <div className={STYLES.avatarBot}>
          <Bot className="size-4" aria-hidden />
        </div>
        <h2 className={STYLES.chatTitle}>AI Property Assistant</h2>
      </header>

      {isBusy ? (
        <div className={STYLES.loadingWrap}>
          <Loader2 className="mr-2 size-5 animate-spin" aria-hidden />
          Connecting…
        </div>
      ) : (
        <div className={STYLES.chatBody}>
          <MessageList messages={messages} isSending={isSending} />
          <ChatComposer
            draft={draft}
            setDraft={setDraft}
            textareaRef={textareaRef}
            sessionId={sessionId}
            isSending={isSending}
            onSend={handleSend}
          />
        </div>
      )}
    </div>
  );
};
