"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PropsWithChildren,
  type RefObject,
} from "react";
import { useRouter } from "next/navigation";

import { useSearchWizard } from "@contexts/search-wizard";
import { getApiErrorMessage } from "@lib/api-errors";
import { intakeSessionsService, type LlmInputResponse } from "@services/intake-sessions";

import { buildExtractedRows, type ExtractedRow } from "../components/search-wizard/modes/smart-chat/build-extracted-rows";
import { INTRO_MESSAGE } from "../components/search-wizard/modes/smart-chat/constants";
import type { ChatMessage } from "../components/search-wizard/modes/smart-chat/types";

const assistantReplyText = (data: LlmInputResponse) =>
  data.next_question?.text?.trim() ||
  (data.is_complete
    ? "Great — we have enough to run your search. Use Search Properties when you're ready."
    : "I've updated what I understood from your message.");

export type SmartChatContextValue = {
  busyBootstrap: boolean;
  draft: string;
  errorMessage: string | null;
  extractedRows: ExtractedRow[];
  handleSearchProperties: () => Promise<void>;
  handleSend: () => Promise<void>;
  isComplete: boolean;
  isSearchBusy: boolean;
  isSending: boolean;
  missingFields: string[];
  messages: ChatMessage[];
  resetToChooser: () => void;
  sessionId: string | null;
  setDraft: (value: string) => void;
  textareaRef: RefObject<HTMLTextAreaElement | null>;
};

const SmartChatContext = createContext<SmartChatContextValue | null>(null);

const useSmartChatState = (): SmartChatContextValue => {
  const router = useRouter();
  const {
    errorMessage,
    isLoadingQuestion,
    isSubmitting,
    onClose,
    resetToChooser,
    sessionId,
    setErrorMessage,
  } = useSearchWizard();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [lastResponse, setLastResponse] = useState<LlmInputResponse | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [isSearchBusy, setIsSearchBusy] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const welcomeSeeded = useRef(false);

  useEffect(() => {
    if (!sessionId || welcomeSeeded.current) {
      return;
    }
    welcomeSeeded.current = true;
    setMessages([
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: INTRO_MESSAGE,
      },
    ]);
  }, [sessionId]);

  useEffect(() => {
    textareaRef.current?.focus();
  }, [sessionId, messages.length]);

  const extractedRows = useMemo(
    () => buildExtractedRows(lastResponse?.extracted ?? null),
    [lastResponse],
  );

  const isComplete = lastResponse?.is_complete ?? false;
  const busyBootstrap = isLoadingQuestion && !sessionId;
  const missingFields = lastResponse?.missing_fields ?? [];

  const handleSend = useCallback(async () => {
    const text = draft.trim();
    if (!sessionId || !text || isSending || isSubmitting) {
      return;
    }

    setIsSending(true);
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
      setLastResponse(data);
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: assistantReplyText(data),
        },
      ]);
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err));
      setMessages((m) => m.filter((x) => x.id !== userMsg.id));
      setDraft(text);
    } finally {
      setIsSending(false);
    }
  }, [draft, isSending, isSubmitting, sessionId, setErrorMessage]);

  const handleSearchProperties = useCallback(async () => {
    if (!sessionId || !isComplete || isSearchBusy) {
      return;
    }
    setIsSearchBusy(true);
    setErrorMessage(null);
    try {
      await intakeSessionsService.completeSession(sessionId);
      onClose();
      router.push("/");
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err));
    } finally {
      setIsSearchBusy(false);
    }
  }, [isComplete, isSearchBusy, onClose, router, sessionId, setErrorMessage]);

  return {
    busyBootstrap,
    draft,
    errorMessage,
    extractedRows,
    handleSearchProperties,
    handleSend,
    isComplete,
    isSearchBusy,
    isSending,
    missingFields,
    messages,
    resetToChooser,
    sessionId,
    setDraft,
    textareaRef,
  };
};

export const SmartChatProvider = ({ children }: PropsWithChildren) => {
  const value = useSmartChatState();
  return (
    <SmartChatContext.Provider value={value}>{children}</SmartChatContext.Provider>
  );
};

export const useSmartChat = (): SmartChatContextValue => {
  const ctx = useContext(SmartChatContext);
  if (!ctx) {
    throw new Error("useSmartChat must be used within SmartChatProvider");
  }
  return ctx;
};
