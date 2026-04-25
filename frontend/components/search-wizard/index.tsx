"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ChevronLeft } from "lucide-react";

import { Button } from "@components/ui/button";
import { getApiErrorMessage } from "@lib/api-errors";
import {
  intakeSessionsService,
  type IntakeSessionQuestion,
} from "@services/intake-sessions";

import { QuestionInput } from "./question-input";
import { SummaryPanel } from "./summary-panel";
import type { AnswerValue, WizardAnswers, WizardQuestion } from "./types";
import {
  getDefaultAnswer,
  isQuestionComplete,
} from "./utils";
import { ASSUMED_TOTAL_QUESTION_STEPS } from "./constants";
import { ProgressBar } from "./progress-bar";

type SearchWizardProps = {
  onClose: () => void;
};

const OVERLAY_CLASS_NAME = [
  "fixed inset-0 z-50 flex min-h-screen",
  "bg-slate-950/70 backdrop-blur-sm",
].join(" ");

const PANEL_CLASS_NAME = [
  "flex min-h-screen w-full flex-col overflow-hidden",
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

const MAIN_COLUMN_CLASS_NAME = "flex w-full max-w-2xl flex-col gap-3 justify-self-center";

const SECTION_WITHOUT_PANEL_CLASS_NAME = [
  "flex w-full flex-col rounded-xl",
  "border border-border/70 bg-background/90",
  "p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.55)] sm:p-5",
].join(" ");

const MAIN_COLUMN_WITH_SUMMARY_CLASS_NAME =
  "flex w-full min-w-0 flex-col gap-3";

const SECTION_WITH_PANEL_CLASS_NAME = [
  "flex w-full min-h-[22rem] flex-col rounded-xl",
  "border border-border/70 bg-background/90",
  "p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.55)] sm:p-5",
].join(" ");

export const SearchWizard = ({ onClose }: SearchWizardProps) => {
  const router = useRouter();
  const showSummaryPanel = false;
  const [stepIndex, setStepIndex] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<WizardQuestion | null>(
    null,
  );
  const [answers, setAnswers] = useState<WizardAnswers>({});
  const [isLoadingQuestion, setLoadingQuestion] = useState(true);
  const [isSubmitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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

  useEffect(() => {
    let isActive = true;

    const startSession = async () => {
      setLoadingQuestion(true);
      setErrorMessage(null);

      try {
        const response = await intakeSessionsService.createSession();
        const firstQuestion = mapApiQuestionToWizardQuestion(
          response.first_question,
        );

        if (!isActive) {
          return;
        }

        setSessionId(response.session_id);
        setCurrentQuestion(firstQuestion);
        setAnswers({
          [firstQuestion.id]: getDefaultAnswer(firstQuestion),
        });
        setStepIndex(0);
      } catch (error) {
        if (!isActive) {
          return;
        }

        setErrorMessage(getApiErrorMessage(error));
      } finally {
        if (isActive) {
          setLoadingQuestion(false);
        }
      }
    };

    void startSession();

    return () => {
      isActive = false;
    };
  }, []);

  const currentAnswer = currentQuestion ? answers[currentQuestion.id] : undefined;
  const canContinue =
    currentQuestion != null &&
    isQuestionComplete(currentQuestion, currentAnswer);

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

  const handleNext = async () => {
    if (
      !currentQuestion ||
      !sessionId ||
      !canContinue ||
      isLoadingQuestion ||
      isSubmitting
    ) {
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);

    try {
      const answerToSubmit = answers[currentQuestion.id];

      if (answerToSubmit === undefined) {
        return;
      }

      const response = await intakeSessionsService.submitAnswer(sessionId, {
        key: currentQuestion.id,
        answers: answerToSubmit,
      });

      if (response.next_question == null) {
        onClose();
        router.push("/dashboard");
        return;
      }

      const nextQuestion = mapApiQuestionToWizardQuestion(response.next_question);

      setCurrentQuestion(nextQuestion);
      setAnswers((current) => ({
        ...current,
        [nextQuestion.id]:
          current[nextQuestion.id] ?? getDefaultAnswer(nextQuestion),
      }));
      setStepIndex((current) => current + 1);
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  const isBusy = isLoadingQuestion || isSubmitting;

  return (
    <div className={OVERLAY_CLASS_NAME}>
      <div className={PANEL_CLASS_NAME}>
        <div className={CONTENT_CLASS_NAME}>

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
                    onAnswerChange={(value) =>
                      updateAnswer(currentQuestion.id, value)
                    }
                    onMultiSelectToggle={(value) =>
                      handleToggleMultiSelect(currentQuestion.id, value)
                    }
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
                    onClick={onClose}
                    disabled={isBusy}
                  >
                    <ChevronLeft className="size-4" aria-hidden />
                    Back
                  </Button>

                  <Button
                    size="default"
                    className="h-9 px-3 text-sm"
                    onClick={() => void handleNext()}
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
        </div>
      </div>
    </div>
  );
};

const mapApiQuestionToWizardQuestion = (
  question: IntakeSessionQuestion,
): WizardQuestion => {
  const normalizedType = question.type.trim().toLowerCase();

  if (normalizedType === "text" || normalizedType === "textarea") {
    return {
      id: question.key,
      kind: "text",
      title: question.text,
      description: "",
      required: true,
    };
  }

  return {
    id: question.key,
    kind: "text",
    title: question.text,
    description: "",
    required: true,
  };
};
