import { formatInteger, formatMetricNumber, formatMoney } from "@lib/utils";
import type { IntakeSessionQuestion } from "@services/intake-sessions";

import {
  type RangeQuestion,
  type AnswerValue,
  type RangeAnswerValue,
  type WizardAnswers,
  type WizardQuestion,
} from "./types";

export const getRangeQuestionUnit = (question: RangeQuestion): string | undefined =>
  question.options?.unit;

export const getQuestionInputDisplayTitle = (question: WizardQuestion): string => {
  if (question.kind === "range") {
    const unit = getRangeQuestionUnit(question);
    if (unit) {
      return `${question.title} (${unit.trim()})`;
    }
  }
  return question.title;
};

export const parseQuestion = (question: IntakeSessionQuestion): WizardQuestion => {
  const baseQuestion = {
    id: question.key,
    title: question.title,
    description: question.text,
    required: true,
  };

  switch (question.type) {
    case "multi-select":
      return {
        ...baseQuestion,
        kind: "multi-select",
        options: Array.isArray(question.options) ? question.options : [],
      };
    case "range": {
      const raw = question.options;
      const rangeOptions =
        raw != null && typeof raw === "object" && !Array.isArray(raw)
          ? (raw as Record<string, string>)
          : undefined;
      return {
        ...baseQuestion,
        kind: "range",
        ...(rangeOptions != null && Object.keys(rangeOptions).length > 0 ? { options: rangeOptions } : {}),
      };
    }
    case "location":
      return { ...baseQuestion, kind: "location" };
    default:
      return { ...baseQuestion, kind: "text" };
  }
};

const rangeTitleKey = (title: string) => title.trim().toLowerCase();

export const formatRangeValue = (value: number, questionTitle: string, unit?: string) => {
  const key = rangeTitleKey(questionTitle);
  if (key === "price") {
    return formatMoney(value, { integerThreshold: 0 });
  }
  if (key === "size") {
    return unit ? `${formatInteger(value)} ${unit}` : formatInteger(value);
  }
  return formatMetricNumber(value);
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
      const unit = getRangeQuestionUnit(question);
      return `${formatRangeValue(answer.min, question.title, unit)} - ${formatRangeValue(answer.max, question.title, unit)}`;
    }
    return "Not answered";
  }

  if (question.kind === "location") {
    if (typeof answer === "string" && answer.trim().length > 0) {
      return answer.trim();
    }
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
        return answer.label.trim();
      }
      if (typeof answer.input === "string" && answer.input.trim().length > 0) {
        return answer.input.trim();
      }
    }
    return "Not answered";
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
      const o = answer as { label?: string; input?: string; city?: string };
      return (
        (typeof o.label === "string" && o.label.trim().length > 0) ||
        (typeof o.input === "string" && o.input.trim().length > 0) ||
        (typeof o.city === "string" && o.city.trim().length > 0)
      );
    }
    return false;
  }

  return typeof answer === "string" && answer.trim().length > 0;
};