// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SectionHeading } from "@components/landing/section-heading";

describe("SectionHeading", () => {
  it("renders the heading text", () => {
    render(<SectionHeading>Featured listings</SectionHeading>);
    expect(screen.getByRole("heading", { name: "Featured listings" })).toBeInTheDocument();
  });

  it("renders a description when provided", () => {
    render(<SectionHeading desc="Find what you need">Listings</SectionHeading>);
    expect(screen.getByText("Find what you need")).toBeInTheDocument();
  });

  it("does not render a description element when desc is absent", () => {
    render(<SectionHeading>Listings</SectionHeading>);
    expect(screen.queryByText(/description/i)).not.toBeInTheDocument();
  });

  it("renders actions when provided", () => {
    render(
      <SectionHeading actions={<button>View all</button>}>Listings</SectionHeading>,
    );
    expect(screen.getByRole("button", { name: "View all" })).toBeInTheDocument();
  });

  it("applies custom className to the wrapper", () => {
    const { container } = render(<SectionHeading className="mb-4 text-white">Title</SectionHeading>);
    expect(container.firstChild).toHaveClass("mb-4", "text-white");
  });
});
