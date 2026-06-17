// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TextQuestionInput } from "@components/search/wizard/question-input/text";
import { NumberField } from "@components/search/wizard/question-input/number";
import type { TextQuestion } from "@components/search/wizard/types";

const TEXT_QUESTION: TextQuestion = {
  id: "neighborhood",
  kind: "text",
  title: "Preferred neighborhood?",
  description: "Enter your preferred area.",
};

describe("TextQuestionInput", () => {
  it("renders an input", () => {
    render(<TextQuestionInput question={TEXT_QUESTION} answer="" onChange={vi.fn()} />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("displays the current answer value", () => {
    render(
      <TextQuestionInput question={TEXT_QUESTION} answer="Midtown" onChange={vi.fn()} />,
    );
    expect(screen.getByRole("textbox")).toHaveValue("Midtown");
  });

  it("calls onChange with the new value when user types", async () => {
    const onChange = vi.fn();
    render(<TextQuestionInput question={TEXT_QUESTION} answer="" onChange={onChange} />);
    await userEvent.type(screen.getByRole("textbox"), "D");
    expect(onChange).toHaveBeenCalledWith("D");
  });
});

describe("NumberField", () => {
  it("renders a labeled number input", () => {
    render(<NumberField id="min" label="Minimum" value={null} onChange={vi.fn()} />);
    expect(screen.getByLabelText("Minimum")).toBeInTheDocument();
    expect(screen.getByLabelText("Minimum")).toHaveAttribute("type", "number");
  });

  it("displays the current value", () => {
    render(<NumberField id="min" label="Minimum" value={500000} onChange={vi.fn()} />);
    expect(screen.getByLabelText("Minimum")).toHaveValue(500000);
  });

  it("shows empty string when value is null", () => {
    render(<NumberField id="min" label="Minimum" value={null} onChange={vi.fn()} />);
    expect(screen.getByLabelText("Minimum")).toHaveValue(null);
  });

  it("renders a placeholder when provided", () => {
    render(
      <NumberField id="min" label="Minimum" value={null} onChange={vi.fn()} placeholder="e.g. 100000" />,
    );
    expect(screen.getByPlaceholderText("e.g. 100000")).toBeInTheDocument();
  });

  it("applies min attribute", () => {
    render(<NumberField id="min" label="Minimum" value={null} onChange={vi.fn()} min={1000} />);
    expect(screen.getByLabelText("Minimum")).toHaveAttribute("min", "1000");
  });
});
