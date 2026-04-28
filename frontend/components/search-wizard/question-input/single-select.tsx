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
  <div className="grid gap-2.5 md:grid-cols-3">
    {question.options.map((option, index) => (
      <SelectOptionCard
        key={option.value}
        label={option.label}
        hint={option.hint}
        selected={answer === option.value}
        autoFocus={index === 0}
        onClick={() => onChange(option.value)}
      />
    ))}
  </div>
);
