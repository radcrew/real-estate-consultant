"use client";

import type { AnswerValue, WizardQuestion } from "../types";

import { MultiSelectQuestionInput } from "./multi-select";
import { QuestionInputShell } from "./shell";
import { RangeQuestionInput } from "./range";
import { SingleSelectQuestionInput } from "./single-select";
import { TextQuestionInput } from "./text";

type QuestionInputProps = {
  question: WizardQuestion;
  answer: AnswerValue | undefined;
  onAnswerChange: (value: AnswerValue) => void;
  onMultiSelectToggle: (value: string) => void;
};

export const QuestionInput = ({
  question,
  answer,
  onAnswerChange,
  onMultiSelectToggle,
}: QuestionInputProps) => (
  <QuestionInputShell question={question}>
    {question.kind === "text" && (
      <TextQuestionInput
        question={question}
        answer={typeof answer === "string" ? answer : ""}
        onChange={onAnswerChange}
      />
    )}

    {question.kind === "single-select" && (
      <SingleSelectQuestionInput
        question={question}
        answer={typeof answer === "string" ? answer : ""}
        onChange={onAnswerChange}
      />
    )}

    {question.kind === "multi-select" && (
      <MultiSelectQuestionInput
        question={question}
        answer={Array.isArray(answer) ? answer : []}
        onToggle={onMultiSelectToggle}
      />
    )}

    {question.kind === "range" && (
      <RangeQuestionInput
        question={question}
        answer={typeof answer === "number" ? answer : question.min}
        onChange={onAnswerChange}
      />
    )}
  </QuestionInputShell>
);
