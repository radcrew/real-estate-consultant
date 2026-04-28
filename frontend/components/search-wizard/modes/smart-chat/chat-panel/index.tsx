"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Bot, Loader2 } from "lucide-react";

import { useSearchWizard } from "@contexts/search-wizard";
import { useIntakeSessions } from "@hooks/use-intake-sessions";
import { getApiErrorMessage } from "@lib/api-errors";
import type { LlmInputResponse } from "@services/intake-sessions";

import type { ChatMessage } from "../types";
import { ChatComposer } from "./chat-composer";
import { MessageList } from "./message-list";
import { styles } from "../styles";

type ChatPanelProps = {
  onLlmSuccess: (data: LlmInputResponse) => void;
};

export const ChatPanel = ({ onLlmSuccess }: ChatPanelProps) => {
  const { submitLlmInput } = useIntakeSessions();
  const {
    clearLlmChatBootstrap,
    errorMessage,
    isLoadingQuestion,
    isSubmitting,
    llmChatBootstrap,
    sessionId,
    setErrorMessage,
  } = useSearchWizard();

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

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };
    setMessages((m) => [...m, userMsg]);

    try {
      const data = await submitLlmInput(sessionId, {
        input: text,
        mode: "llm",
      });
      onLlmSuccess(data);

      const followUp = data.next_question?.text?.trim();
      if (followUp) {
        setMessages((m) => [
          ...m,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: followUp,
          },
        ]);
      }
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err));
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
    sessionId,
    setErrorMessage,
    submitLlmInput,
  ]);

  return (
    <div className={styles.chatColumn}>
      <header className={styles.chatHeader}>
        <div className={styles.avatarBot}>
          <Bot className="size-4" aria-hidden />
        </div>
        <h2 className={styles.chatTitle}>AI Property Assistant</h2>
      </header>

      {errorMessage && (
        <div className={`${styles.errorBanner} mx-4 mt-3 sm:mx-5`}>{errorMessage}</div>
      )}

      {isBusy ? (
        <div className={styles.loadingWrap}>
          <Loader2 className="mr-2 size-5 animate-spin" aria-hidden />
          Connecting…
        </div>
      ) : (
        <div className={styles.chatBody}>
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
