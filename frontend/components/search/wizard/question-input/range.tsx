"use client";

import type { ChangeEvent } from "react";

import { NumberField } from "./number";
import type { RangeAnswerValue, RangeQuestion } from "../types";

type RangeQuestionInputProps = {
  question: RangeQuestion;
  answer: RangeAnswerValue;
  onChange: (value: RangeAnswerValue) => void;
};

export const RangeQuestionInput = ({
  question,
  answer,
  onChange,
}: RangeQuestionInputProps) => {
  const unit = question.options?.unit;

  const handleChange =
    (field: keyof RangeAnswerValue) =>
    (event: ChangeEvent<HTMLInputElement>) => {
      const raw = event.target.value.trim();
      const num = raw === "" ? null : Math.max(0, Number(raw));
      onChange({ ...answer, [field]: num });
    };

  const isInvalid =
    answer.min !== null && answer.max !== null && answer.min > answer.max;

  return (
    <div className="grid w-full gap-3 sm:grid-cols-2">
      <NumberField
        id={`${question.id}-min`}
        label={unit ? `Min (${unit})` : "Min"}
        value={answer.min}
        onChange={handleChange("min")}
        min={0}
        autoFocus
      />
      <NumberField
        id={`${question.id}-max`}
        label={unit ? `Max (${unit})` : "Max"}
        value={answer.max}
        onChange={handleChange("max")}
        min={0}
      />
      {isInvalid && (
        <p className="sm:col-span-2 text-sm text-red-500">
          Max must be greater than or equal to Min.
        </p>
      )}
    </div>
  );
};
