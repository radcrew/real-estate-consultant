// @vitest-environment jsdom
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RangeQuestionInput } from "@components/search/wizard/question-input/range";
import type { RangeQuestion } from "@components/search/wizard/types";

const QUESTION: RangeQuestion = {
  id: "size",
  kind: "range",
  title: "Size",
  description: "Enter min and max square footage.",
  options: { unit: "sqft" },
};

const QUESTION_NO_UNIT: RangeQuestion = {
  id: "budget",
  kind: "range",
  title: "Budget",
  description: "Enter your budget.",
};

describe("RangeQuestionInput", () => {
  it("renders Min and Max fields with unit suffix", () => {
    render(<RangeQuestionInput question={QUESTION} answer={{ min: null, max: null }} onChange={vi.fn()} />);
    expect(screen.getByLabelText("Min (sqft)")).toBeInTheDocument();
    expect(screen.getByLabelText("Max (sqft)")).toBeInTheDocument();
  });

  it("renders plain Min and Max when no unit", () => {
    render(
      <RangeQuestionInput question={QUESTION_NO_UNIT} answer={{ min: null, max: null }} onChange={vi.fn()} />,
    );
    expect(screen.getByLabelText("Min")).toBeInTheDocument();
    expect(screen.getByLabelText("Max")).toBeInTheDocument();
  });

  it("calls onChange with updated min when the min field changes", () => {
    const onChange = vi.fn();
    render(
      <RangeQuestionInput question={QUESTION} answer={{ min: null, max: null }} onChange={onChange} />,
    );
    fireEvent.change(screen.getByLabelText("Min (sqft)"), { target: { value: "500" } });
    expect(onChange).toHaveBeenCalledWith({ min: 500, max: null });
  });

  it("calls onChange with updated max when the max field changes", () => {
    const onChange = vi.fn();
    render(
      <RangeQuestionInput question={QUESTION} answer={{ min: null, max: null }} onChange={onChange} />,
    );
    fireEvent.change(screen.getByLabelText("Max (sqft)"), { target: { value: "2000" } });
    expect(onChange).toHaveBeenCalledWith({ min: null, max: 2000 });
  });

  it("shows an error when min exceeds max", () => {
    render(
      <RangeQuestionInput question={QUESTION} answer={{ min: 5000, max: 1000 }} onChange={vi.fn()} />,
    );
    expect(screen.getByText(/max must be greater than or equal to min/i)).toBeInTheDocument();
  });

  it("does not show an error when min is null", () => {
    render(
      <RangeQuestionInput question={QUESTION} answer={{ min: null, max: 1000 }} onChange={vi.fn()} />,
    );
    expect(screen.queryByText(/max must be greater/i)).not.toBeInTheDocument();
  });

  it("treats empty input as null", () => {
    const onChange = vi.fn();
    render(
      <RangeQuestionInput question={QUESTION} answer={{ min: 500, max: null }} onChange={onChange} />,
    );
    fireEvent.change(screen.getByLabelText("Min (sqft)"), { target: { value: "" } });
    expect(onChange).toHaveBeenCalledWith({ min: null, max: null });
  });
});
