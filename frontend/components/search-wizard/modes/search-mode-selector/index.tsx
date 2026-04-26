"use client";

import type { ReactNode } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ListChecks,
  Sparkles,
} from "lucide-react";

import { Button } from "@components/ui/button";

import { useSearchWizard } from "@contexts/search-wizard";
import { GuidedQuestionnaire } from "../guided-questionnaire";
import { SmartChat } from "../smart-chat";

import { styles } from "./styles";

export const SearchModeSelector = () => {
  const {
    errorMessage,
    isBusy,
    isGuidedFormOpen,
    isSmartChatOpen,
    onClose,
    showSmartChat,
    startGuidedForm,
  } = useSearchWizard();

  if (isGuidedFormOpen) {
    return <GuidedQuestionnaire />;
  }

  if (isSmartChatOpen) {
    return <SmartChat />;
  }

  return (
    <div className={styles.chooserWrapper}>
      <div className={styles.chooserIntro}>
        <h2 className={styles.chooserHeading}>
          How would you like to search?
        </h2>
        <p className={styles.chooserSubtitle}>
          Choose the search style that works best for you.
        </p>
      </div>

      {errorMessage && (
        <div className={styles.chooserError}>{errorMessage}</div>
      )}

      <div className={styles.chooserGrid}>
        <section className={styles.choiceCard}>
          <div className={styles.choiceIconCellSky}>
            <ListChecks className="size-6" aria-hidden />
          </div>

          <div className={styles.choiceBodyTop}>
            <h3 className={styles.choiceTitle}>Step-by-Step Form</h3>
            <p className={styles.choiceDescription}>
              Answer questions one at a time. Best if you know exactly what you
              want.
            </p>
          </div>

          <div className={styles.choiceBullets}>
            <ChoiceBullet>Guided 5-step process</ChoiceBullet>
            <ChoiceBullet>All criteria are explicit</ChoiceBullet>
            <ChoiceBullet>Easy to refine each field</ChoiceBullet>
          </div>

          <Button
            variant="outline"
            className={styles.choiceFormCta}
            onClick={startGuidedForm}
            disabled={isBusy}
          >
            {isBusy ? "Loading form..." : "Use Form"}
            <ArrowRight className="size-4" aria-hidden />
          </Button>
        </section>

        <section className={styles.choiceCard}>
          <div className={styles.choiceCornerBadge}>AI</div>

          <div className={styles.choiceIconCellViolet}>
            <Sparkles className="size-6" aria-hidden />
          </div>

          <div className={styles.choiceBodyTop}>
            <h3 className={styles.choiceTitle}>AI Chat</h3>
            <p className={styles.choiceDescription}>
              Just describe your needs. AI extracts your criteria and asks
              follow-ups.
            </p>
          </div>

          <div className={styles.choiceBullets}>
            <ChoiceBullet>Conversational</ChoiceBullet>
            <ChoiceBullet>AI fills the form for you</ChoiceBullet>
            <ChoiceBullet>Asks for missing info</ChoiceBullet>
          </div>

          <Button
            className={styles.choiceAiCta}
            onClick={showSmartChat}
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
        className={styles.chooserBackLink}
      >
        <ArrowLeft className="size-4" aria-hidden />
        Back to Home
      </button>
    </div>
  );
};

const ChoiceBullet = ({ children }: { children: ReactNode }) => (
  <div className={styles.bulletRow}>
    <Check className={styles.bulletCheck} aria-hidden />
    <span>{children}</span>
  </div>
);
