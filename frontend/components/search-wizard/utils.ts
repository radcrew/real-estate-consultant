import type { IntakeSessionQuestion } from "@services/intake-sessions";

import type { AnswerValue, SummaryRow, WizardAnswers, WizardQuestion } from "./types";

export const mapApiQuestionToWizardQuestion = (
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

export const formatRangeValue = (value: number, unit?: string) => {
  if (unit === "$") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(value);
  }

  if (unit === "SF") {
    return `${new Intl.NumberFormat("en-US").format(value)} SF`;
  }

  return `${value}${unit ? ` ${unit}` : ""}`;
};

export const getDefaultAnswer = (question: WizardQuestion): AnswerValue => {
  if (question.kind === "multi-select") {
    return [];
  }

  if (question.kind === "range") {
    return question.min;
  }

  return "";
};

export const createInitialAnswers = (questions: WizardQuestion[]): WizardAnswers =>
  Object.fromEntries(
    questions.map((question) => [question.id, getDefaultAnswer(question)]),
  );

export const isQuestionComplete = (
  question: WizardQuestion,
  answer: AnswerValue | undefined,
) => {
  if (!question.required) {
    return true;
  }

  if (question.kind === "multi-select") {
    return Array.isArray(answer) && answer.length > 0;
  }

  if (question.kind === "range") {
    return typeof answer === "number";
  }

  return typeof answer === "string" && answer.trim().length > 0;
};

export const buildSummaryRows = (
  questions: WizardQuestion[],
  answers: WizardAnswers,
): SummaryRow[] =>
  questions.map((question) => {
    const answer = answers[question.id];

    if (question.kind === "multi-select") {
      const selected = Array.isArray(answer) ? answer : [];

      return {
        id: question.id,
        label: question.title,
        value:
          selected.length > 0
            ? question.options
                .filter((option) => selected.includes(option.value))
                .map((option) => option.label)
                .join(", ")
            : "Not answered",
      };
    }

    if (question.kind === "single-select") {
      return {
        id: question.id,
        label: question.title,
        value:
          question.options.find((option) => option.value === answer)?.label ??
          "Not answered",
      };
    }

    if (question.kind === "range") {
      return {
        id: question.id,
        label: question.title,
        value:
          typeof answer === "number"
            ? formatRangeValue(answer, question.unit)
            : "Not answered",
      };
    }

    return {
      id: question.id,
      label: question.title,
      value: typeof answer === "string" && answer.trim() ? answer : "Not answered",
    };
  });
