export type QuestionOption = {
  label: string;
  value: string;
  hint?: string;
};

type BaseQuestion<TKind extends string> = {
  id: string;
  kind: TKind;
  title: string;
  description: string;
  required?: boolean;
};

type SelectQuestion<TKind extends "single-select" | "multi-select"> =
  BaseQuestion<TKind> & {
    options: QuestionOption[];
  };

export type SingleSelectQuestion = SelectQuestion<"single-select">;

export type MultiSelectQuestion = SelectQuestion<"multi-select">;

export type TextQuestion = BaseQuestion<"text">;

export type LocationQuestion = BaseQuestion<"location">;

export type RangeQuestion = BaseQuestion<"range"> & {
  unit?: string;
};

export type WizardQuestion =
  | SingleSelectQuestion
  | MultiSelectQuestion
  | TextQuestion
  | LocationQuestion
  | RangeQuestion;

export type RangeAnswerValue = {
  min: number | null;
  max: number | null;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type AnswerValue = any;
export type WizardAnswers = Record<string, AnswerValue>;

export type SummaryRow = {
  id: string;
  label: string;
  value: string;
};
