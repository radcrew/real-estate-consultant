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
  <div className="grid gap-3 md:grid-cols-3">
    {question.options.map((option) => (
      <SelectOptionCard
        key={option.value}
        label={option.label}
        hint={option.hint}
        selected={answer.includes(option.value)}
        rounded={false}
        onClick={() => onToggle(option.value)}
      />
    ))}
  </div>
);
