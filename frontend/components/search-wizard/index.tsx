"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowRight, ChevronLeft, X } from "lucide-react";

import { Button } from "@components/ui/button";

import { QuestionInput } from "./question-input";
import { WIZARD_QUESTIONS } from "./questions";
import { SummaryPanel } from "./summary-panel";
import type { AnswerValue, WizardAnswers } from "./types";
import {
  buildSummaryRows,
  createInitialAnswers,
  isQuestionComplete,
} from "./utils";
import { ProgressBar } from "./progress-bar";

type SearchWizardProps = {
  onClose: () => void;
};

const OVERLAY_CLASS_NAME = [
  "fixed inset-0 z-50 flex min-h-screen",
  "bg-slate-950/70 backdrop-blur-sm",
].join(" ");

const PANEL_CLASS_NAME = [
  "relative flex min-h-screen w-full flex-col overflow-hidden",
  "bg-[radial-gradient(circle_at_top_left,_rgba(245,158,11,0.2),_transparent_30%),linear-gradient(180deg,_rgba(255,251,235,0.98),_rgba(248,250,252,0.98))]",
  "text-foreground",
].join(" ");

const CONTENT_CLASS_NAME = [
  "mx-auto flex w-full max-w-5xl flex-1 flex-col",
  "px-4 pt-5 pb-4 sm:px-6 lg:px-8",
].join(" ");

const SUMMARY_GRID_CLASS_NAME = [
  "mt-5 grid flex-1 gap-4",
  "justify-items-center items-start",
].join(" ");

const SUMMARY_GRID_WITH_PANEL_CLASS_NAME = [
  "mt-5 grid flex-1 gap-4",
  "lg:grid-cols-[minmax(0,1.35fr)_320px]",
].join(" ");

const SECTION_WITHOUT_PANEL_CLASS_NAME = [
  "flex w-full max-w-2xl justify-self-center flex-col",
  "border border-border/70 bg-background/90",
  "p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.55)] sm:p-5",
].join(" ");

const SECTION_WITH_PANEL_CLASS_NAME = [
  "flex w-full min-h-[22rem] flex-col",
  "border border-border/70 bg-background/90",
  "p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.55)] sm:p-5",
].join(" ");

export const SearchWizard = ({ onClose }: SearchWizardProps) => {
  const showSummaryPanel = false;
  const [stepIndex, setStepIndex] = useState(0);
  const [answers, setAnswers] = useState<WizardAnswers>(() =>
    createInitialAnswers(WIZARD_QUESTIONS),
  );

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleEscape);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleEscape);
    };
  }, [onClose]);

  const currentQuestion = WIZARD_QUESTIONS[stepIndex];
  const currentAnswer = answers[currentQuestion.id];
  const isLastStep = stepIndex === WIZARD_QUESTIONS.length - 1;
  const canContinue = isQuestionComplete(currentQuestion, currentAnswer);

  const summaryRows = useMemo(
    () => buildSummaryRows(WIZARD_QUESTIONS, answers),
    [answers],
  );

  const updateAnswer = (questionId: string, value: AnswerValue) => {
    setAnswers((current) => ({
      ...current,
      [questionId]: value,
    }));
  };

  const handleToggleMultiSelect = (questionId: string, value: string) => {
    const current = answers[questionId];
    const selected = Array.isArray(current) ? current : [];

    updateAnswer(
      questionId,
      selected.includes(value)
        ? selected.filter((item) => item !== value)
        : [...selected, value],
    );
  };

  const handleNext = () => {
    if (!canContinue || isLastStep) {
      return;
    }

    setStepIndex((current) => current + 1);
  };

  return (
    <div className={OVERLAY_CLASS_NAME}>
      <div className={PANEL_CLASS_NAME}>

        <ProgressBar stepIndex={stepIndex}/>

        <div className={CONTENT_CLASS_NAME}>
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1.5">
              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                Search intake
              </p>
              <div className="space-y-0.5">
                <h2 className="text-lg font-semibold tracking-tight sm:text-xl">
                  Define the search in a few quick steps
                </h2>
              </div>
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="rounded-full border border-border/70 bg-background/80"
              onClick={onClose}
              aria-label="Close search wizard"
            >
              <X className="size-4" />
            </Button>
          </div>

          <div
            className={
              showSummaryPanel
                ? SUMMARY_GRID_WITH_PANEL_CLASS_NAME
                : SUMMARY_GRID_CLASS_NAME
            }
          >
            <section
              className={
                showSummaryPanel
                  ? SECTION_WITH_PANEL_CLASS_NAME
                  : SECTION_WITHOUT_PANEL_CLASS_NAME
              }
            >
              <QuestionInput
                question={currentQuestion}
                answer={currentAnswer}
                stepIndex={stepIndex}
                totalSteps={WIZARD_QUESTIONS.length}
                onAnswerChange={(value) => updateAnswer(currentQuestion.id, value)}
                onMultiSelectToggle={(value) =>
                  handleToggleMultiSelect(currentQuestion.id, value)
                }
              />

              <div className="mt-4 flex flex-col gap-2.5 border-t border-border/70 pt-3 sm:flex-row sm:items-center sm:justify-between">
                <Button
                  variant="outline"
                  size="default"
                  className="h-9 px-3 text-sm"
                  onClick={() => setStepIndex((current) => Math.max(0, current - 1))}
                  disabled={stepIndex === 0}
                >
                  <ChevronLeft className="size-4" aria-hidden />
                  Back
                </Button>

                <Button
                  size="default"
                  className="h-9 px-3 text-sm"
                  onClick={isLastStep ? onClose : handleNext}
                  disabled={!canContinue}
                >
                  {isLastStep ? "Finish for now" : "Continue"}
                  {!isLastStep && <ArrowRight className="size-4" aria-hidden />}
                </Button>
              </div>
            </section>

            {showSummaryPanel && <SummaryPanel rows={summaryRows} />}
          </div>
        </div>
      </div>
    </div>
  );
};
