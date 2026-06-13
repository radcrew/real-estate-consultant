"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, SlidersHorizontal, Wand2 } from "lucide-react";

import { useSearchWizard } from "@contexts/search-wizard";
import { getApiErrorMessage } from "@utils/common";
import { formatCriteriaValue } from "@utils/search/criteria";
import { intakeSessionsService, type LlmInputResponse } from "@services/intake-sessions";

import { STYLES } from "../../styles";

type SidePanelProps = {
  lastResponse: LlmInputResponse | null;
};

export const SidePanel = ({ lastResponse }: SidePanelProps) => {
  const router = useRouter();
  const { sessionId, setErrorMessage, resetToChooser, onClose } = useSearchWizard();
  const [isSearchBusy, setSearchBusy] = useState(false);

  const criteria = lastResponse?.criteria ?? {};
  const missingFields = lastResponse?.missing_fields ?? [];
  const questionTitles = lastResponse?.question_titles ?? {};
  const criteriaEntries = Object.entries(criteria).filter(([, v]) => v !== null && v !== undefined);

  const handleSearchProperties = useCallback(async () => {
    if (!sessionId || isSearchBusy) return;
    setSearchBusy(true);
    setErrorMessage(null);
    try {
      const completed = await intakeSessionsService.completeSession(sessionId);
      const profileId = completed.search_profile_id;
      if (!profileId) {
        setErrorMessage("Search profile was not created. Please try again.");
        return;
      }
      onClose();
      router.push(`/search/${profileId}`);
    } catch (err) {
      setErrorMessage(getApiErrorMessage(err));
    } finally {
      setSearchBusy(false);
    }
  }, [isSearchBusy, onClose, router, sessionId, setErrorMessage]);

  return (
    <aside className={STYLES.sidebar}>
      <div className={STYLES.card}>
        <div className={STYLES.cardHeader}>
          <div className={STYLES.cardTitleRow}>
            <SlidersHorizontal className="size-4 text-primary-600" aria-hidden />
            <h3 className={STYLES.cardTitle}>Extracted Criteria</h3>
          </div>
        </div>

        {criteriaEntries.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Criteria will appear here as you describe what you're looking for.
          </p>
        ) : (
          <ul className="mt-2 space-y-2">
            {criteriaEntries.map(([key, value]) => (
              <li key={key} className="flex justify-between gap-3 text-sm">
                <span className="capitalize text-muted-foreground">{key.replace(/_/g, " ")}</span>
                <span className="font-medium text-neutral-800 dark:text-neutral-200 text-right">
                  {formatCriteriaValue(value)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {missingFields.length > 0 && (
        <div className={STYLES.considerCard}>
          <p className={STYLES.considerTitle}>Optional details:</p>
          <ul className={STYLES.considerList}>
            {missingFields.map((f) => (
              <li key={f}>{questionTitles[f] ?? f.replace(/_/g, " ")}</li>
            ))}
          </ul>
        </div>
      )}

      <button
        type="button"
        className={STYLES.searchCta}
        disabled={isSearchBusy || !sessionId}
        onClick={handleSearchProperties}
      >
        {isSearchBusy ? (
          <Loader2 className="size-4 animate-spin" aria-hidden />
        ) : (
          <Wand2 className="size-4" aria-hidden />
        )}
        Search Properties
      </button>

      <button type="button" className={STYLES.switchLink} onClick={resetToChooser}>
        <ArrowLeft className="size-4" aria-hidden />
        Switch mode
      </button>
    </aside>
  );
};
