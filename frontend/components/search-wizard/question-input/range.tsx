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
  const handleChange =
    (field: keyof RangeAnswerValue) =>
    (event: ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value.trim();
      onChange({
        ...answer,
        [field]: value === "" ? null : Number(value),
      });
    };

  return (
    <div className="grid w-full gap-3 sm:grid-cols-2">
      <NumberField
        id={`${question.id}-min`}
        label={`Min ${question.unit ?? ""}`}
        value={answer.min}
        onChange={handleChange("min")}
      />
      <NumberField
        id={`${question.id}-max`}
        label={`Max ${question.unit ?? ""}`}
        value={answer.max}
        onChange={handleChange("max")}
      />
    </div>
  );
};
