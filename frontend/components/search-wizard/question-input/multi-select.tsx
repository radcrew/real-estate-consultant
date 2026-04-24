"use client";

import type { MultiSelectQuestion } from "../types";

import { SelectOptionCard } from "./select";

type MultiSelectQuestionInputProps = {
  question: MultiSelectQuestion;
  answer: string[];
  onToggle: (value: string) => void;
};

export const MultiSelectQuestionInput = ({
  question,
  answer,
  onToggle,
}: MultiSelectQuestionInputProps) => (
  <div className="grid gap-2.5 md:grid-cols-3">
    {question.options.map((option) => (
      <SelectOptionCard
        key={option.value}
        label={option.label}
        hint={option.hint}
        selected={answer.includes(option.value)}
        onClick={() => onToggle(option.value)}
      />
    ))}
  </div>
);
