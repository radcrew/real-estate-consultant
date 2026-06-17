// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProgressBar } from "@components/search/wizard/progress-bar";

describe("ProgressBar", () => {
  it("shows step label", () => {
    render(<ProgressBar stepIndex={0} totalSteps={5} />);
    expect(screen.getByText("Step 1 of 5")).toBeInTheDocument();
  });

  it("shows 0% complete on first step", () => {
    render(<ProgressBar stepIndex={0} totalSteps={5} />);
    expect(screen.getByText("0% complete")).toBeInTheDocument();
  });

  it("shows correct step and percent on mid step", () => {
    render(<ProgressBar stepIndex={2} totalSteps={5} />);
    expect(screen.getByText("Step 3 of 5")).toBeInTheDocument();
    expect(screen.getByText("40% complete")).toBeInTheDocument();
  });

  it("shows 100% on last step", () => {
    render(<ProgressBar stepIndex={5} totalSteps={5} />);
    expect(screen.getByText("100% complete")).toBeInTheDocument();
  });

  it("renders a progressbar with aria-valuenow", () => {
    render(<ProgressBar stepIndex={1} totalSteps={4} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "25");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
  });

  it("guards against totalSteps of 0 (treats as 1)", () => {
    render(<ProgressBar stepIndex={0} totalSteps={0} />);
    expect(screen.getByText("Step 1 of 1")).toBeInTheDocument();
  });

  it("clamps negative stepIndex to 0%", () => {
    render(<ProgressBar stepIndex={-1} totalSteps={5} />);
    expect(screen.getByText("0% complete")).toBeInTheDocument();
  });
});
