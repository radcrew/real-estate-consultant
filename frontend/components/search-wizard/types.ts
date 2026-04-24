export type SingleSelectQuestion = {
  id: string;
  kind: "single-select";
  title: string;
  description: string;
  required?: boolean;
  options: Array<{
    label: string;
    value: string;
    hint?: string;
  }>;
};

export type MultiSelectQuestion = {
  id: string;
  kind: "multi-select";
  title: string;
  description: string;
  required?: boolean;
  options: Array<{
    label: string;
    value: string;
    hint?: string;
  }>;
};

export type TextQuestion = {
  id: string;
  kind: "text";
  title: string;
  description: string;
  required?: boolean;
  placeholder?: string;
};

export type RangeQuestion = {
  id: string;
  kind: "range";
  title: string;
  description: string;
  required?: boolean;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  minLabel?: string;
  maxLabel?: string;
};

export type WizardQuestion =
  | SingleSelectQuestion
  | MultiSelectQuestion
  | TextQuestion
  | RangeQuestion;

export type AnswerValue = string | string[] | number;
export type WizardAnswers = Record<string, AnswerValue>;

export type SummaryRow = {
  id: string;
  label: string;
  value: string;
};
