import type { IntakeSessionQuestion } from "@services/intake-sessions";

import type { WizardQuestion } from "./types";

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
