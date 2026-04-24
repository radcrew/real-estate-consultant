"use client";

import { formatRangeValue } from "../utils";
import type { RangeQuestion } from "../types";

type RangeQuestionInputProps = {
  question: RangeQuestion;
  answer: number;
  onChange: (value: number) => void;
};

export const RangeQuestionInput = ({
  question,
  answer,
  onChange,
}: RangeQuestionInputProps) => (
  <div className="max-w-3xl space-y-5">
    <div className="flex items-end justify-between gap-4 border border-border/70 bg-background px-4 py-3">
      <div>
        <p className="text-xs text-muted-foreground sm:text-sm">Current value</p>
        <p className="text-2xl font-semibold sm:text-3xl">
          {formatRangeValue(answer, question.unit)}
        </p>
      </div>
      <p className="max-w-xs text-right text-xs text-muted-foreground sm:text-sm">
        Drag the slider to set the floor requirement for this search.
      </p>
    </div>

    <div className="space-y-2.5">
      <input
        id={question.id}
        type="range"
        min={question.min}
        max={question.max}
        step={question.step ?? 1}
        value={answer}
        onChange={(event) => onChange(Number(event.target.value))}
        className="h-2 w-full cursor-pointer appearance-none bg-transparent accent-primary"
      />
      <div className="flex items-center justify-between text-xs text-muted-foreground sm:text-sm">
        <span>{question.minLabel ?? question.min}</span>
        <span>{question.maxLabel ?? question.max}</span>
      </div>
    </div>
  </div>
);
