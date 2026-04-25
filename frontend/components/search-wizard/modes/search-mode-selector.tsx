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

import { GuidedQuestionnaire } from "./guided-questionnaire";
import { useSearchWizard } from "../context/search-wizard";
import { SmartChat } from "./smart-chat";

const CHOOSER_WRAPPER_CLASS_NAME =
  "mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center py-10";

const CHOOSER_BADGE_CLASS_NAME = [
  "inline-flex items-center justify-center rounded-md border border-border/70",
  "bg-background px-3 py-1 text-xs font-semibold text-foreground shadow-sm",
].join(" ");

const CHOOSER_GRID_CLASS_NAME = "mt-8 grid w-full gap-4 md:grid-cols-2";

const CHOICE_CARD_CLASS_NAME = [
  "relative flex min-h-[19.75rem] flex-col rounded-xl border border-slate-200",
  "bg-white px-6 py-6 shadow-[0_18px_50px_-40px_rgba(15,23,42,0.35)]",
].join(" ");

const BULLET_ROW_CLASS_NAME =
  "flex items-start gap-2 text-sm leading-6 text-slate-600";

const CHOICE_BULLET_CHECK_CLASS_NAME =
  "mt-1 size-4 shrink-0 text-emerald-500";

const CHOOSER_INTRO_CLASS_NAME = "mt-6 max-w-2xl text-center";

const CHOOSER_HEADING_CLASS_NAME =
  "text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl";

const CHOOSER_SUBTITLE_CLASS_NAME = "mt-3 text-lg text-slate-500";

const CHOOSER_ERROR_CLASS_NAME = [
  "mt-6 w-full max-w-3xl rounded-lg border border-destructive/30 bg-destructive/5",
  "px-4 py-3 text-sm text-destructive",
].join(" ");

const CHOICE_ICON_CELL_SKY_CLASS_NAME =
  "flex size-12 items-center justify-center rounded-lg bg-sky-100 text-blue-600";

const CHOICE_ICON_CELL_VIOLET_CLASS_NAME =
  "flex size-12 items-center justify-center rounded-lg bg-violet-100 text-violet-600";

const CHOICE_CORNER_BADGE_CLASS_NAME = [
  "absolute right-4 top-4 rounded-md bg-violet-600 px-3 py-1 text-xs font-semibold uppercase",
  "tracking-[0.18em] text-white",
].join(" ");

const CHOICE_TITLE_CLASS_NAME =
  "text-2xl font-semibold tracking-tight text-slate-950";

const CHOICE_DESCRIPTION_CLASS_NAME = "mt-3 text-lg leading-8 text-slate-500";

const CHOICE_BULLETS_CLASS_NAME = "mt-5 space-y-1.5";

const CHOICE_BODY_TOP_CLASS_NAME = "mt-5";

const CHOICE_FORM_CTA_CLASS_NAME =
  "mt-auto h-11 rounded-md border-slate-200 text-base font-medium shadow-none";

const CHOICE_AI_CTA_CLASS_NAME = [
  "mt-5 h-11 rounded-md border-violet-700 bg-gradient-to-r from-violet-600 to-indigo-600",
  "text-base font-medium text-white shadow-none hover:from-violet-600 hover:to-indigo-500",
].join(" ");

const CHOOSER_BACK_LINK_CLASS_NAME = [
  "mt-10 inline-flex items-center gap-2 text-sm font-medium text-slate-900",
  "transition-colors hover:text-slate-600",
].join(" ");

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
    <div className={CHOOSER_WRAPPER_CLASS_NAME}>
      <div className={CHOOSER_BADGE_CLASS_NAME}>Step 1 of 2</div>

      <div className={CHOOSER_INTRO_CLASS_NAME}>
        <h2 className={CHOOSER_HEADING_CLASS_NAME}>
          How would you like to search?
        </h2>
        <p className={CHOOSER_SUBTITLE_CLASS_NAME}>
          Choose the search style that works best for you.
        </p>
      </div>

      {errorMessage && (
        <div className={CHOOSER_ERROR_CLASS_NAME}>{errorMessage}</div>
      )}

      <div className={CHOOSER_GRID_CLASS_NAME}>
        <section className={CHOICE_CARD_CLASS_NAME}>
          <div className={CHOICE_ICON_CELL_SKY_CLASS_NAME}>
            <ListChecks className="size-6" aria-hidden />
          </div>

          <div className={CHOICE_BODY_TOP_CLASS_NAME}>
            <h3 className={CHOICE_TITLE_CLASS_NAME}>Step-by-Step Form</h3>
            <p className={CHOICE_DESCRIPTION_CLASS_NAME}>
              Answer questions one at a time. Best if you know exactly what you
              want.
            </p>
          </div>

          <div className={CHOICE_BULLETS_CLASS_NAME}>
            <ChoiceBullet>Guided 5-step process</ChoiceBullet>
            <ChoiceBullet>All criteria are explicit</ChoiceBullet>
            <ChoiceBullet>Easy to refine each field</ChoiceBullet>
          </div>

          <Button
            variant="outline"
            className={CHOICE_FORM_CTA_CLASS_NAME}
            onClick={() => void startGuidedForm()}
            disabled={isBusy}
          >
            {isBusy ? "Loading form..." : "Use Form"}
            <ArrowRight className="size-4" aria-hidden />
          </Button>
        </section>

        <section className={CHOICE_CARD_CLASS_NAME}>
          <div className={CHOICE_CORNER_BADGE_CLASS_NAME}>AI</div>

          <div className={CHOICE_ICON_CELL_VIOLET_CLASS_NAME}>
            <Sparkles className="size-6" aria-hidden />
          </div>

          <div className={CHOICE_BODY_TOP_CLASS_NAME}>
            <h3 className={CHOICE_TITLE_CLASS_NAME}>AI Chat</h3>
            <p className={CHOICE_DESCRIPTION_CLASS_NAME}>
              Just describe your needs. AI extracts your criteria and asks
              follow-ups.
            </p>
          </div>

          <div className={CHOICE_BULLETS_CLASS_NAME}>
            <ChoiceBullet>Conversational</ChoiceBullet>
            <ChoiceBullet>AI fills the form for you</ChoiceBullet>
            <ChoiceBullet>Asks for missing info</ChoiceBullet>
          </div>

          <Button
            className={CHOICE_AI_CTA_CLASS_NAME}
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
        className={CHOOSER_BACK_LINK_CLASS_NAME}
      >
        <ArrowLeft className="size-4" aria-hidden />
        Back to Home
      </button>
    </div>
  );
};

const ChoiceBullet = ({ children }: { children: ReactNode }) => (
  <div className={BULLET_ROW_CLASS_NAME}>
    <Check className={CHOICE_BULLET_CHECK_CLASS_NAME} aria-hidden />
    <span>{children}</span>
  </div>
);
