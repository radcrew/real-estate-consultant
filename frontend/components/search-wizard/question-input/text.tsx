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
  <div className="space-y-2">
    <label
      htmlFor={question.id}
      className="text-xs font-medium text-foreground"
    >
      Enter your preferred location
    </label>
    <Input
      id={question.id}
      value={answer}
      onChange={(event) => onChange(event.target.value)}
      placeholder={question.placeholder}
      className="h-9 border-border/80 bg-background px-3 text-sm"
    />
  </div>
);
