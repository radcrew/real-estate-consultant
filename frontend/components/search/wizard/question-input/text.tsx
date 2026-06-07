"use client";

import { Input } from "@components/ui/voyager/input";

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
    <Input
      id={question.id}
      value={answer}
      onChange={(event) => onChange(event.target.value)}
      autoFocus
    />
  </div>
);
