"use client";

import { type ReactNode, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ListChecks,
  Sparkles,
} from "lucide-react";

import { ButtonPrimary } from "@components/ui/button-primary";
import { ButtonThird } from "@components/ui/button-third";

import { useSearchWizard } from "@contexts/search-wizard";

import { STYLES } from "./styles";

export const SearchModeSelector = () => {
  const {
    isBusy,
    onClose,
    startSmartChat,
    startGuidedForm,
  } = useSearchWizard();
  const [starting, setStarting] = useState<"form" | "chat" | null>(null);
  // Once a choice is made, keep BOTH buttons disabled through the redirect —
  // not just while `isBusy`, which can briefly flip off during navigation.
  const isStarting = isBusy || starting !== null;

  // Disable both buttons while starting; on failure the start call resolves
  // `false` (it stays on the selector), so re-enable them to allow a retry.
  // On success this view unmounts during the redirect.
  const handleStart = async (
    choice: "form" | "chat",
    start: () => Promise<boolean>,
  ) => {
    if (isStarting) return;
    setStarting(choice);
    const ok = await start();
    if (!ok) {
      setStarting(null);
    }
  };

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

          <ButtonThird
            className={STYLES.choiceFormCta}
            onClick={() => handleStart("form", startGuidedForm)}
            disabled={isStarting}
          >
            {starting === "form" ? "Loading form..." : "Use Form"}
            <ArrowRight className="ml-2 size-4" aria-hidden />
          </ButtonThird>
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

          <ButtonPrimary
            className={STYLES.choiceAiCta}
            onClick={() => handleStart("chat", startSmartChat)}
            disabled={isStarting}
          >
            {starting === "chat" ? "Loading chat..." : "Use AI Chat"}
            <Sparkles className="ml-2 size-4" aria-hidden />
          </ButtonPrimary>
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
