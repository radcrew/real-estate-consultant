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
  <div className="space-y-2.5">
    <label
      htmlFor={question.id}
      className="text-xs font-medium text-foreground sm:text-sm"
    >
      Enter your preferred location
    </label>
    <Input
      id={question.id}
      value={answer}
      onChange={(event) => onChange(event.target.value)}
      placeholder={question.placeholder}
      className="h-12 border-border/80 bg-background px-4 text-sm sm:text-base"
    />
  </div>
);
