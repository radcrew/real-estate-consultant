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
  <div className="max-w-xl space-y-4">
    <div className="flex items-end justify-between gap-3 border border-border/70 bg-background px-3 py-2.5">
      <div>
        <p className="text-xs text-muted-foreground">Current value</p>
        <p className="text-lg font-semibold sm:text-xl">
          {formatRangeValue(answer, question.unit)}
        </p>
      </div>
      <p className="max-w-[14rem] text-right text-xs text-muted-foreground">
        Drag the slider to set the floor requirement for this search.
      </p>
    </div>

    <div className="space-y-2">
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
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{question.minLabel ?? question.min}</span>
        <span>{question.maxLabel ?? question.max}</span>
      </div>
    </div>
  </div>
);
