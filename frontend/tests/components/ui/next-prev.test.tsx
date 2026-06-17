// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { NextPrev } from "@components/ui/next-prev";

describe("NextPrev", () => {
  it("renders both Prev and Next buttons by default", () => {
    render(<NextPrev />);
    expect(screen.getByTitle("Prev")).toBeInTheDocument();
    expect(screen.getByTitle("Next")).toBeInTheDocument();
  });

  it("calls onClickPrev when Prev is clicked", async () => {
    const onClickPrev = vi.fn();
    render(<NextPrev onClickPrev={onClickPrev} />);
    await userEvent.click(screen.getByTitle("Prev"));
    expect(onClickPrev).toHaveBeenCalledOnce();
  });

  it("calls onClickNext when Next is clicked", async () => {
    const onClickNext = vi.fn();
    render(<NextPrev onClickNext={onClickNext} />);
    await userEvent.click(screen.getByTitle("Next"));
    expect(onClickNext).toHaveBeenCalledOnce();
  });

  it("hides Prev button when onlyNext is true", () => {
    render(<NextPrev onlyNext />);
    expect(screen.queryByTitle("Prev")).not.toBeInTheDocument();
    expect(screen.getByTitle("Next")).toBeInTheDocument();
  });

  it("hides Next button when onlyPrev is true", () => {
    render(<NextPrev onlyPrev />);
    expect(screen.getByTitle("Prev")).toBeInTheDocument();
    expect(screen.queryByTitle("Next")).not.toBeInTheDocument();
  });
});
