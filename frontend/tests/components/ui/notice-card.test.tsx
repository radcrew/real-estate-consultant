// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NoticeCard } from "@components/ui/notice-card";

describe("NoticeCard", () => {
  it("renders children", () => {
    render(<NoticeCard>No results found.</NoticeCard>);
    expect(screen.getByText("No results found.")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<NoticeCard className="mt-8">Content</NoticeCard>);
    expect(container.firstChild).toHaveClass("mt-8");
  });

  it("includes the base border and padding classes", () => {
    const { container } = render(<NoticeCard>Content</NoticeCard>);
    expect(container.firstChild).toHaveClass("rounded-2xl", "p-10", "text-center");
  });
});
