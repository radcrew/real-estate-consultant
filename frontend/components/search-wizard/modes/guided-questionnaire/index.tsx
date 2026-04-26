"use client";

import { ArrowRight, ChevronLeft } from "lucide-react";

import { Button } from "@components/ui/button";

import { useSearchWizard } from "@contexts/search-wizard";
import { ProgressBar } from "../../progress-bar";
import { QuestionInput } from "../../question-input";
import { SummaryPanel } from "../../summary-panel";

import { styles } from "./styles";

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

  return (
    <div className={styles.summaryGrid}>
      <div className={styles.progressRow}>
        <ProgressBar stepIndex={stepIndex} totalSteps={totalSteps} />
      </div>

      <div className={styles.mainColumn}>
        <section className={styles.section}>
          {errorMessage && (
            <div className={styles.errorBanner}>{errorMessage}</div>
          )}

          {currentQuestion ? (
            <QuestionInput
              question={currentQuestion}
              answer={currentAnswer}
              onAnswerChange={updateCurrentAnswer}
              onMultiSelectToggle={toggleCurrentMultiSelect}
            />
          ) : (
            <div className={styles.loadingState}>
              {isLoadingQuestion
                ? "Loading your questionnaire..."
                : "We couldn't load the questionnaire."}
            </div>
          )}

          <div className={styles.actionsRow}>
            <Button
              variant="outline"
              size="default"
              className={styles.buttonDefault}
              onClick={goPrev}
              disabled={isBusy}
            >
              <ChevronLeft className="size-4" aria-hidden />
              Back
            </Button>

            <Button
              size="default"
              className={styles.buttonDefault}
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

      <div className={styles.summaryColumn}>
        <SummaryPanel rows={summaryRows} />
      </div>
    </div>
  );
};
