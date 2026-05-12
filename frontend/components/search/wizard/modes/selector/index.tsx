"use client";

import type { ReactNode } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ListChecks,
  Sparkles,
} from "lucide-react";

import { Button } from "@components/ui/buttons";

import { useSearchWizard } from "@contexts/search-wizard";

import { STYLES } from "./styles";

export const SearchModeSelector = () => {
  const {
    errorMessage,
    isBusy,
    onClose,
    startSmartChat,
    startGuidedForm,
  } = useSearchWizard();

  return (
    <div className={STYLES.chooserWrapper}>
      <div className={STYLES.chooserIntro}>
        <h2 className={STYLES.chooserHeading}>
          How would you like to search?
        </h2>
        <p className={STYLES.chooserSubtitle}>
          Choose the search style that works best for you.
        </p>
      </div>

      {errorMessage && (
        <div className={STYLES.chooserError}>{errorMessage}</div>
      )}

      <div className={STYLES.chooserGrid}>
        <section className={STYLES.choiceCard}>
          <div className={STYLES.choiceIconCellSky}>
            <ListChecks className="size-6" aria-hidden />
          </div>

          <div className={STYLES.choiceBodyTop}>
            <h3 className={STYLES.choiceTitle}>Step-by-Step Form</h3>
            <p className={STYLES.choiceDescription}>
              Answer questions one at a time. Best if you know exactly what you
              want.
            </p>
          </div>

          <div className={STYLES.choiceBullets}>
            <ChoiceBullet>Guided step-by-step process</ChoiceBullet>
            <ChoiceBullet>All criteria are explicit</ChoiceBullet>
            <ChoiceBullet>Easy to refine each field</ChoiceBullet>
          </div>

          <Button
            variant="outline"
            className={STYLES.choiceFormCta}
            onClick={startGuidedForm}
            disabled={isBusy}
          >
            {isBusy ? "Loading form..." : "Use Form"}
            <ArrowRight className="size-4" aria-hidden />
          </Button>
        </section>

        <section className={STYLES.choiceCard}>
          <div className={STYLES.choiceCornerBadge}>AI</div>

          <div className={STYLES.choiceIconCellViolet}>
            <Sparkles className="size-6" aria-hidden />
          </div>

          <div className={STYLES.choiceBodyTop}>
            <h3 className={STYLES.choiceTitle}>AI Chat</h3>
            <p className={STYLES.choiceDescription}>
              Just describe your needs. AI extracts your criteria and asks
              follow-ups.
            </p>
          </div>

          <div className={STYLES.choiceBullets}>
            <ChoiceBullet>Conversational</ChoiceBullet>
            <ChoiceBullet>AI fills the form for you</ChoiceBullet>
            <ChoiceBullet>Asks for missing info</ChoiceBullet>
          </div>

          <Button
            className={STYLES.choiceAiCta}
            onClick={startSmartChat}
            disabled={isBusy}
          >
            Use AI Chat
            <Sparkles className="size-4" aria-hidden />
          </Button>
        </section>
      </div>

      <button
        type="button"
        onClick={onClose}
        className={STYLES.chooserBackLink}
      >
        <ArrowLeft className="size-4" aria-hidden />
        Back to Home
      </button>
    </div>
  );
};

const ChoiceBullet = ({ children }: { children: ReactNode }) => (
  <div className={STYLES.bulletRow}>
    <Check className={STYLES.bulletCheck} aria-hidden />
    <span>{children}</span>
  </div>
);
