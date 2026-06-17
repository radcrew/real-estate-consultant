// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { QuestionInputShell } from "@components/search/wizard/question-input/shell";
import type { WizardQuestion } from "@components/search/wizard/types";

const QUESTION: WizardQuestion = {
  id: "budget",
  kind: "range",
  title: "What is your budget?",
  description: "Enter your minimum and maximum budget.",
};

describe("QuestionInputShell", () => {
  it("renders the question title", () => {
    render(<QuestionInputShell question={QUESTION}>content</QuestionInputShell>);
    expect(screen.getByRole("heading", { name: /what is your budget/i })).toBeInTheDocument();
  });

  it("renders the question description", () => {
    render(<QuestionInputShell question={QUESTION}>content</QuestionInputShell>);
    expect(
      screen.getByText("Enter your minimum and maximum budget."),
    ).toBeInTheDocument();
  });

  it("renders children", () => {
    render(
      <QuestionInputShell question={QUESTION}>
        <input type="number" aria-label="min" />
      </QuestionInputShell>,
    );
    expect(screen.getByLabelText("min")).toBeInTheDocument();
  });
});
