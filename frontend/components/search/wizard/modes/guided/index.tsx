"use client";

import { ArrowRight, ChevronLeft } from "lucide-react";

import { Button } from "@components/ui/buttons";

import { useSearchWizard } from "@contexts/search-wizard";
import { ProgressBar } from "../../progress-bar";
import { QuestionInput } from "../../question-input";
import { SummaryPanel } from "../../summary-panel";

import { STYLES } from "./styles";

export const GuidedQuestionnaire = () => {
  const {
    canContinue,
    currentAnswer,
    currentQuestion,
    errorMessage,
    goNext,
    goPrev,
    isBusy,
    isLoadingQuestion,
    isSubmitting,
    summaryRows,
    stepIndex,
    totalSteps,
    toggleCurrentMultiSelect,
    updateCurrentAnswer,
  } = useSearchWizard();
  const isLastStep = stepIndex >= totalSteps - 1;

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Enter") {
      goNext();
    }
  };

  return (
    <div className={STYLES.summaryGrid}>
      <div className={STYLES.progressRow}>
        <ProgressBar stepIndex={stepIndex} totalSteps={totalSteps} />
      </div>

      <div className={STYLES.mainColumn}>
        <section
          className={STYLES.section}
          onKeyDown={handleKeyDown}
        >
          {errorMessage && (
            <div className={STYLES.errorBanner}>{errorMessage}</div>
          )}

          {currentQuestion ? (
            <QuestionInput
              key={currentQuestion.id}
              question={currentQuestion}
              answer={currentAnswer}
              onAnswerChange={updateCurrentAnswer}
              onMultiSelectToggle={toggleCurrentMultiSelect}
            />
          ) : (
            <div className={STYLES.loadingState}>
              {isLoadingQuestion
                ? "Loading your questionnaire..."
                : "We couldn't load the questionnaire."}
            </div>
          )}

          <div className={STYLES.actionsRow}>
            <Button
              variant="outline"
              size="default"
              className={STYLES.buttonDefault}
              onClick={goPrev}
              disabled={isBusy}
            >
              <ChevronLeft className="size-4" aria-hidden />
              Back
            </Button>

            <Button
              size="default"
              className={STYLES.buttonDefault}
              onClick={goNext}
              disabled={!canContinue || isBusy}
            >
              {isSubmitting
                ? isLastStep
                  ? "Searching..."
                  : "Saving..."
                : isLastStep
                  ? "Search"
                  : "Continue"}
              <ArrowRight className="size-4" aria-hidden />
            </Button>
          </div>
        </section>
      </div>

      <div className={STYLES.summaryColumn}>
        <SummaryPanel rows={summaryRows} />
      </div>
    </div>
  );
};
