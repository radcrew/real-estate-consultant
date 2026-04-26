import type {
  ApiQuestionSchema,
  AnswerValue,
  RangeAnswerValue,
  WizardAnswers,
  WizardQuestion,
} from "./types";

const normalizeQuestionType = (questionType: string) =>
  questionType.trim().toLowerCase();

export const parseApiQuestion = (question: ApiQuestionSchema): WizardQuestion => {
  const normalizedType = normalizeQuestionType(question.type);

  if (normalizedType === "multi_select" || normalizedType === "multi-select") {
    return {
      id: question.key,
      kind: "multi-select",
      title: question.key,
      description: question.text,
      required: true,
      options: question.options ?? [],
    };
  }

  if (normalizedType === "range") {
    return {
      id: question.key,
      kind: "range",
      title: question.key,
      description: question.text,
      required: true,
    };
  }

  return {
    id: question.key,
    kind: "text",
    title: question.key,
    description: question.text,
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

  return typeof answer === "string" && answer.trim().length > 0;
};