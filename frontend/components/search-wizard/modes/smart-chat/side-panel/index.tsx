"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, SlidersHorizontal, Wand2 } from "lucide-react";

import { useSearchWizard } from "@contexts/search-wizard";
import { useIntakeSessions } from "@hooks/use-intake-sessions";
import { getApiErrorMessage } from "@lib/api-errors";
import type { LlmInputResponse } from "@services/intake-sessions";

import { styles } from "../styles";

type SidePanelProps = {
  lastResponse: LlmInputResponse | null;
};

export const SidePanel = ({ lastResponse }: SidePanelProps) => {
  const router = useRouter();
  const { completeSession } = useIntakeSessions();
  const { sessionId, setErrorMessage, resetToChooser, onClose } = useSearchWizard();
  const [isSearchBusy, setIsSearchBusy] = useState(false);

  const isComplete = lastResponse?.is_complete ?? false;
  const missingFields = lastResponse?.missing_fields ?? [];

  const handleSearchProperties = useCallback(async () => {
    if (!sessionId || !isComplete || isSearchBusy) {
      return;
    }
    setIsSearchBusy(true);
    setErrorMessage(null);
    try {
      await completeSession(sessionId);
      onClose();
      router.push("/");
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err));
    } finally {
      setIsSearchBusy(false);
    }
  }, [
    completeSession,
    isComplete,
    isSearchBusy,
    onClose,
    router,
    sessionId,
    setErrorMessage,
  ]);

  return (
    <aside className={styles.sidebar}>
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitleRow}>
            <SlidersHorizontal className="size-4 text-amber-600" aria-hidden />
            <h3 className={styles.cardTitle}>Extracted Criteria</h3>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">
          Structured criteria from this chat will appear here once the API provides them.
        </p>
      </div>

      {missingFields.length > 0 && (
        <div className={styles.missingCard}>
          <p className={styles.missingTitle}>Still needed:</p>
          <ul className={styles.missingList}>
            {missingFields.map((f) => (
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
  );
};
