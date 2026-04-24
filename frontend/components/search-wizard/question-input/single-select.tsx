"use client";

import type { SingleSelectQuestion } from "../types";

import { SelectOptionCard } from "./select";

type SingleSelectQuestionInputProps = {
  question: SingleSelectQuestion;
  answer: string;
  onChange: (value: string) => void;
};

export const SingleSelectQuestionInput = ({
  question,
  answer,
  onChange,
}: SingleSelectQuestionInputProps) => (
  <div className="grid gap-3 md:grid-cols-3">
    {question.options.map((option) => (
      <SelectOptionCard
        key={option.value}
        label={option.label}
        hint={option.hint}
        selected={answer === option.value}
        onClick={() => onChange(option.value)}
      />
    ))}
  </div>
);
