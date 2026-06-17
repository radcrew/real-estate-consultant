// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SummaryPanel } from "@components/search/wizard/summary-panel";

const ROWS = [
  { id: "budget", label: "Budget", value: "Up to $500K" },
  { id: "type", label: "Property type", value: "House" },
];

describe("SummaryPanel", () => {
  it("shows placeholder text when rows is empty", () => {
    render(<SummaryPanel rows={[]} />);
    expect(
      screen.getByText("Answers will appear here as you complete each step."),
    ).toBeInTheDocument();
  });

  it("shows a count of 0 when rows is empty", () => {
    render(<SummaryPanel rows={[]} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders all row labels and values", () => {
    render(<SummaryPanel rows={ROWS} />);
    expect(screen.getByText("Budget")).toBeInTheDocument();
    expect(screen.getByText("Up to $500K")).toBeInTheDocument();
    expect(screen.getByText("Property type")).toBeInTheDocument();
    expect(screen.getByText("House")).toBeInTheDocument();
  });

  it("shows the correct row count", () => {
    render(<SummaryPanel rows={ROWS} />);
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("does not show the placeholder when rows are present", () => {
    render(<SummaryPanel rows={ROWS} />);
    expect(
      screen.queryByText("Answers will appear here as you complete each step."),
    ).not.toBeInTheDocument();
  });
});
