// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SelectOptionCard } from "@components/search/wizard/question-input/select";
import { SingleSelectQuestionInput } from "@components/search/wizard/question-input/select/single";
import { MultiSelectQuestionInput } from "@components/search/wizard/question-input/select/multi";
import type { MultiSelectQuestion, SingleSelectQuestion } from "@components/search/wizard/types";

const SINGLE_QUESTION: SingleSelectQuestion = {
  id: "property-type",
  kind: "single-select",
  title: "Property type",
  description: "Pick one.",
  options: [
    { label: "Industrial", value: "industrial" },
    { label: "Retail", value: "retail" },
    { label: "Office", value: "office" },
  ],
};

const MULTI_QUESTION: MultiSelectQuestion = {
  id: "amenities",
  kind: "multi-select",
  title: "Amenities",
  description: "Pick all that apply.",
  options: [
    { label: "Parking", value: "parking" },
    { label: "Loading dock", value: "loading-dock" },
  ],
};

describe("SelectOptionCard", () => {
  it("renders the label", () => {
    render(<SelectOptionCard label="Industrial" selected={false} onClick={vi.fn()} />);
    expect(screen.getByText("Industrial")).toBeInTheDocument();
  });

  it("renders a hint when provided", () => {
    render(
      <SelectOptionCard label="Office" hint="Modern workspace" selected={false} onClick={vi.fn()} />,
    );
    expect(screen.getByText("Modern workspace")).toBeInTheDocument();
  });

  it("calls onClick when clicked", async () => {
    const onClick = vi.fn();
    render(<SelectOptionCard label="Office" selected={false} onClick={onClick} />);
    await userEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("renders a Factory icon for industrial label", () => {
    const { container } = render(
      <SelectOptionCard label="Industrial" selected={false} onClick={vi.fn()} />,
    );
    expect(container.querySelector("svg")).toBeInTheDocument();
  });
});

describe("SingleSelectQuestionInput", () => {
  it("renders all options as buttons", () => {
    render(<SingleSelectQuestionInput question={SINGLE_QUESTION} answer="" onChange={vi.fn()} />);
    expect(screen.getAllByRole("button")).toHaveLength(3);
    expect(screen.getByText("Industrial")).toBeInTheDocument();
    expect(screen.getByText("Retail")).toBeInTheDocument();
  });

  it("calls onChange with the option value when clicked", async () => {
    const onChange = vi.fn();
    render(
      <SingleSelectQuestionInput question={SINGLE_QUESTION} answer="" onChange={onChange} />,
    );
    await userEvent.click(screen.getByText("Retail"));
    expect(onChange).toHaveBeenCalledWith("retail");
  });
});

describe("MultiSelectQuestionInput", () => {
  it("renders all options", () => {
    render(<MultiSelectQuestionInput question={MULTI_QUESTION} answer={[]} onToggle={vi.fn()} />);
    expect(screen.getByText("Parking")).toBeInTheDocument();
    expect(screen.getByText("Loading dock")).toBeInTheDocument();
  });

  it("calls onToggle with the option value when clicked", async () => {
    const onToggle = vi.fn();
    render(
      <MultiSelectQuestionInput question={MULTI_QUESTION} answer={[]} onToggle={onToggle} />,
    );
    await userEvent.click(screen.getByText("Loading dock"));
    expect(onToggle).toHaveBeenCalledWith("loading-dock");
  });
});
