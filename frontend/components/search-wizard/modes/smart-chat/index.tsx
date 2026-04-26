"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Bot,
  Loader2,
  Send,
  SlidersHorizontal,
  UserRound,
  Wand2,
} from "lucide-react";

import { useSearchWizard } from "@contexts/search-wizard";
import { getApiErrorMessage } from "@lib/api-errors";
import {
  intakeSessionsService,
  type LlmExtracted,
  type LlmInputResponse,
} from "@services/intake-sessions";

import { styles } from "./styles";

const WELCOME_COPY =
  "Hi! I'm here to help you find the right commercial property. Tell me what you're looking for — be as detailed or brief as you want. For example: \"I need a 100k sqft industrial warehouse with 32ft clear height in Chicago for lease, with at least 20 dock doors.\"";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
};

const formatUsd = (n: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);

const titleCase = (s: string) =>
  s.length ? s[0].toUpperCase() + s.slice(1).toLowerCase() : s;

const buildExtractedRows = (extracted: LlmExtracted | null) => {
  if (!extracted) {
    return [];
  }
  const rows: { label: string; value: string }[] = [];
  if (extracted.building_type.length > 0) {
    rows.push({
      label: "Type",
      value: extracted.building_type.map(titleCase).join(", "),
    });
  }
  const { min, max } = extracted.rent_range;
  if (min > 0 || max > 0) {
    rows.push({ label: "Min Budget", value: formatUsd(min) });
    rows.push({ label: "Max Budget", value: formatUsd(max) });
  }
  if (extracted.location?.label?.trim()) {
    rows.push({ label: "Market", value: extracted.location.label });
  }
  const smin = extracted.size_sqft.min;
  const smax = extracted.size_sqft.max;
  if (smin > 0 || smax > 0) {
    rows.push({
      label: "Size",
      value: `${new Intl.NumberFormat("en-US").format(smin)} – ${new Intl.NumberFormat("en-US").format(smax)} SF`,
    });
  }
  return rows;
};

export const SmartChat = () => {
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
        content: WELCOME_COPY,
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

      const assistantText =
        data.next_question?.text?.trim() ||
        (data.is_complete
          ? "Great — we have enough to run your search. Use Search Properties when you're ready."
          : "I've updated what I understood from your message.");

      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: assistantText,
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

  const busyBootstrap = isLoadingQuestion && !sessionId;

  return (
    <div className={styles.layout}>
      <div className={styles.chatColumn}>
        <header className={styles.chatHeader}>
          <div className={styles.avatarBot}>
            <Bot className="size-4" aria-hidden />
          </div>
          <h2 className={styles.chatTitle}>AI Property Assistant</h2>
        </header>

        {errorMessage && (
          <div className={`${styles.errorBanner} mx-4 mt-3 sm:mx-5`}>
            {errorMessage}
          </div>
        )}

        {busyBootstrap ? (
          <div className={styles.loadingWrap}>
            <Loader2 className="mr-2 size-5 animate-spin" aria-hidden />
            Connecting…
          </div>
        ) : (
          <>
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
                  <div className="flex items-center gap-2 rounded-2xl rounded-tl-md border border-border/60 bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
                    <Loader2 className="size-4 animate-spin" aria-hidden />
                    Thinking…
                  </div>
                </div>
              )}
            </div>

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
                      void handleSend();
                    }
                  }}
                  rows={3}
                />
                <button
                  type="button"
                  className={styles.sendButton}
                  aria-label="Send message"
                  disabled={!sessionId || !draft.trim() || isSending}
                  onClick={() => void handleSend()}
                >
                  <Send className="size-4" aria-hidden />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      <aside className={styles.sidebar}>
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitleRow}>
              <SlidersHorizontal className="size-4 text-amber-600" aria-hidden />
              <h3 className={styles.cardTitle}>Extracted Criteria</h3>
            </div>
            <span className={styles.badgeCount}>{extractedRows.length}</span>
          </div>
          {extractedRows.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Criteria extracted from the chat will show up here.
            </p>
          ) : (
            <div className={styles.criteriaTable}>
              {extractedRows.map((row) => (
                <div key={row.label} className={styles.criteriaRow}>
                  <span className={styles.criteriaLabel}>{row.label}</span>
                  <span className={styles.criteriaValue}>{row.value}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {lastResponse && lastResponse.missing_fields.length > 0 && (
          <div className={styles.missingCard}>
            <p className={styles.missingTitle}>Still needed:</p>
            <ul className={styles.missingList}>
              {lastResponse.missing_fields.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </div>
        )}

        <button
          type="button"
          className={styles.searchCta}
          disabled={!isComplete || isSearchBusy || !sessionId}
          onClick={() => void handleSearchProperties()}
        >
          {isSearchBusy ? (
            <Loader2 className="size-4 animate-spin" aria-hidden />
          ) : (
            <Wand2 className="size-4" aria-hidden />
          )}
          Search Properties
        </button>

        <button type="button" className={styles.switchLink} onClick={resetToChooser}>
          <ArrowLeft className="size-4" aria-hidden />
          Switch mode
        </button>
      </aside>
    </div>
  );
};
