"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Bot, Loader2 } from "lucide-react";

import { useSearchWizard } from "@contexts/search-wizard";
import { getApiErrorMessage } from "@utils/common";
import { intakeSessionsService, type LlmInputResponse } from "@services/intake-sessions";

import type { ChatMessage } from "../../types";
import { ChatComposer } from "./composer";
import { MessageList } from "./message-list";
import { STYLES } from "../../styles";

type ChatPanelProps = {
  onLlmSuccess: (data: LlmInputResponse) => void;
};

export const ChatPanel = ({ onLlmSuccess }: ChatPanelProps) => {
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
      const data = await intakeSessionsService.submitLlmInput(sessionId, {
        input: text,
        mode: "llm",
      });
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
  ]);

  return (
    <div className={STYLES.chatColumn}>
      <header className={STYLES.chatHeader}>
        <div className={STYLES.avatarBot}>
          <Bot className="size-4" aria-hidden />
        </div>
        <h2 className={STYLES.chatTitle}>AI Property Assistant</h2>
      </header>

      {errorMessage && (
        <div className={`${STYLES.errorBanner} mx-4 mt-3 sm:mx-5`}>{errorMessage}</div>
      )}

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
