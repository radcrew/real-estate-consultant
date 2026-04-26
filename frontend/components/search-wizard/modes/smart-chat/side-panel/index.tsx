"use client";

import { ArrowLeft, Loader2, SlidersHorizontal, Wand2 } from "lucide-react";

import { useSmartChat } from "@contexts/smart-chat";
import { styles } from "../styles";

export const SidePanel = () => {
  const {
    extractedRows,
    handleSearchProperties,
    isComplete,
    isSearchBusy,
    missingFields,
    resetToChooser,
    sessionId,
  } = useSmartChat();

  return (
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
