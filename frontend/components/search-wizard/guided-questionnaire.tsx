"use client";

import { ArrowRight, ChevronLeft } from "lucide-react";

import { Button } from "@components/ui/button";

import { ASSUMED_TOTAL_QUESTION_STEPS } from "./constants";
import { ProgressBar } from "./progress-bar";
import { QuestionInput } from "./question-input";
import { useSearchWizard } from "./context/search-wizard";
import { SummaryPanel } from "./summary-panel";

const SUMMARY_GRID_CLASS_NAME = [
  "mt-5 grid flex-1 gap-4",
  "justify-items-center items-start",
].join(" ");

const SUMMARY_GRID_WITH_PANEL_CLASS_NAME = [
  "mt-5 grid flex-1 gap-4",
  "lg:grid-cols-[minmax(0,1.35fr)_320px]",
].join(" ");

const MAIN_COLUMN_CLASS_NAME =
  "flex w-full max-w-2xl flex-col gap-3 justify-self-center";

const MAIN_COLUMN_WITH_SUMMARY_CLASS_NAME =
  "flex w-full min-w-0 flex-col gap-3";

const SECTION_WITHOUT_PANEL_CLASS_NAME = [
  "flex w-full flex-col rounded-xl",
  "border border-border/70 bg-background/90",
  "p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.55)] sm:p-5",
].join(" ");

const SECTION_WITH_PANEL_CLASS_NAME = [
  "flex w-full min-h-[22rem] flex-col rounded-xl",
  "border border-border/70 bg-background/90",
  "p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.55)] sm:p-5",
].join(" ");

export const GuidedQuestionnaire = () => {
  const showSummaryPanel = false;
  const {
    canContinue,
    currentAnswer,
    currentQuestion,
    errorMessage,
    goToNextQuestion,
    isBusy,
    isLoadingQuestion,
    isSubmitting,
    resetToChooser,
    stepIndex,
    toggleCurrentMultiSelect,
    updateCurrentAnswer,
  } = useSearchWizard();

  return (
    <div
      className={
        showSummaryPanel
          ? SUMMARY_GRID_WITH_PANEL_CLASS_NAME
          : SUMMARY_GRID_CLASS_NAME
      }
    >
      <div
        className={
          showSummaryPanel
            ? MAIN_COLUMN_WITH_SUMMARY_CLASS_NAME
            : MAIN_COLUMN_CLASS_NAME
        }
      >
        <ProgressBar
          stepIndex={stepIndex}
          totalSteps={ASSUMED_TOTAL_QUESTION_STEPS}
        />

        <section
          className={
            showSummaryPanel
              ? SECTION_WITH_PANEL_CLASS_NAME
              : SECTION_WITHOUT_PANEL_CLASS_NAME
          }
        >
          {errorMessage && (
            <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              {errorMessage}
            </div>
          )}

          {currentQuestion ? (
            <QuestionInput
              question={currentQuestion}
              answer={currentAnswer}
              onAnswerChange={updateCurrentAnswer}
              onMultiSelectToggle={toggleCurrentMultiSelect}
            />
          ) : (
            <div className="py-10 text-sm text-muted-foreground">
              {isLoadingQuestion
                ? "Loading your questionnaire..."
                : "We couldn't load the questionnaire."}
            </div>
          )}

          <div className="mt-8 flex flex-col gap-3 border-t border-border/70 pt-6 sm:flex-row sm:items-center sm:justify-between">
            <Button
              variant="outline"
              size="default"
              className="h-9 px-3 text-sm"
              onClick={resetToChooser}
              disabled={isBusy}
            >
              <ChevronLeft className="size-4" aria-hidden />
              Back
            </Button>

            <Button
              size="default"
              className="h-9 px-3 text-sm"
              onClick={() => void goToNextQuestion()}
              disabled={!canContinue || isBusy}
            >
              {isSubmitting ? "Saving..." : "Continue"}
              <ArrowRight className="size-4" aria-hidden />
            </Button>
          </div>
        </section>
      </div>

      {showSummaryPanel && <SummaryPanel rows={[]} />}
    </div>
  );
};
