"use client";

import { ArrowRight, ChevronLeft } from "lucide-react";

import { Button } from "@components/ui/button";

import { useSearchWizard } from "@contexts/search-wizard";
import { ProgressBar } from "../../progress-bar";
import { QuestionInput } from "../../question-input";
import { SummaryPanel } from "../../summary-panel";

import { styles } from "./styles";

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
    totalSteps,
    toggleCurrentMultiSelect,
    updateCurrentAnswer,
  } = useSearchWizard();

  return (
    <div
      className={
        showSummaryPanel
          ? styles.summaryGridWithPanel
          : styles.summaryGrid
      }
    >
      <div
        className={
          showSummaryPanel
            ? styles.mainColumnWithSummary
            : styles.mainColumn
        }
      >
        <ProgressBar stepIndex={stepIndex} totalSteps={totalSteps} />

        <section
          className={
            showSummaryPanel
              ? styles.sectionWithPanel
              : styles.sectionWithoutPanel
          }
        >
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
              onClick={resetToChooser}
              disabled={isBusy}
            >
              <ChevronLeft className="size-4" aria-hidden />
              Back
            </Button>

            <Button
              size="default"
              className={styles.buttonDefault}
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
