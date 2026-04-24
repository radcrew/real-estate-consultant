"use client";

import { Input } from "@components/ui/input";

import type { TextQuestion } from "../types";

type TextQuestionInputProps = {
  question: TextQuestion;
  answer: string;
  onChange: (value: string) => void;
};

export const TextQuestionInput = ({
  question,
  answer,
  onChange,
}: TextQuestionInputProps) => (
  <div className="max-w-2xl space-y-3">
    <label
      htmlFor={question.id}
      className="text-sm font-medium text-foreground"
    >
      Enter your preferred location
    </label>
    <Input
      id={question.id}
      value={answer}
      onChange={(event) => onChange(event.target.value)}
      placeholder={question.placeholder}
      className="h-14 border-border/80 bg-background px-4 text-base"
    />
  </div>
);
