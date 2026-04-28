import type { IntakeSessionQuestion } from "@services/intake-sessions";

import type { AnswerValue, RangeAnswerValue, WizardAnswers, WizardQuestion } from "./types";

export const parseQuestion = (question: IntakeSessionQuestion): WizardQuestion => {
  const baseQuestion = {
    id: question.key,
    title: question.key,
    description: question.text,
    required: true,
  };

  switch (question.type) {
    case "multi-select":
      return {
        ...baseQuestion,
        kind: "multi-select",
        options: question.options ?? [],
      };
    case "range":
      return { ...baseQuestion, kind: "range" };
    case "location":
      return { ...baseQuestion, kind: "location" };
    default:
      return { ...baseQuestion, kind: "text" };
  }
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

export const formatAnswerForSummary = (
  question: WizardQuestion,
  answer: AnswerValue,
) => {
  if (question.kind === "multi-select") {
    const selectedValues = Array.isArray(answer) ? answer : [];
    const labels = question.options
      .filter((option) => selectedValues.includes(option.value))
      .map((option) => option.label);
    return labels.length > 0 ? labels.join(", ") : "Not answered";
  }

  if (question.kind === "range") {
    if (
      typeof answer === "object" &&
      answer != null &&
      !Array.isArray(answer) &&
      typeof answer.min === "number" &&
      typeof answer.max === "number"
    ) {
      return `${formatRangeValue(answer.min, question.unit)} - ${formatRangeValue(answer.max, question.unit)}`;
    }
    return "Not answered";
  }

  if (question.kind === "location") {
    if (
      typeof answer === "object" &&
      answer != null &&
      !Array.isArray(answer)
    ) {
      const parts = [answer.city, answer.state, answer.country].filter(Boolean);
      if (parts.length > 0) {
        return parts.join(", ");
      }
      if (typeof answer.label === "string" && answer.label.trim().length > 0) {
        return answer.label;
      }
      if (typeof answer.input === "string" && answer.input.trim().length > 0) {
        return answer.input;
      }
    }

    return typeof answer === "string" && answer.trim().length > 0
      ? answer
      : "Not answered";
  }

  return typeof answer === "string" && answer.trim().length > 0
    ? answer
    : "Not answered";
};

export const getDefaultAnswer = (question: WizardQuestion): AnswerValue => {
  if (question.kind === "multi-select") {
    return [];
  }

  if (question.kind === "range") {
    return { min: null, max: null };
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
    if (typeof answer !== "object" || answer == null || Array.isArray(answer)) {
      return false;
    }

    const rangeAnswer = answer as RangeAnswerValue;

    return (
      typeof rangeAnswer.min === "number" &&
      typeof rangeAnswer.max === "number" &&
      rangeAnswer.min <= rangeAnswer.max
    );
  }

  if (question.kind === "location") {
    if (typeof answer === "string") {
      return answer.trim().length > 0;
    }
    if (typeof answer === "object" && answer != null && !Array.isArray(answer)) {
      return (
        typeof answer.label === "string" ||
        typeof answer.input === "string" ||
        typeof answer.city === "string"
      );
    }
    return false;
  }

  return typeof answer === "string" && answer.trim().length > 0;
};