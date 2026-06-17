// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { HowItWorks } from "@components/landing/how-it-works";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

describe("HowItWorks", () => {
  it("renders the section heading", () => {
    render(<HowItWorks />);
    expect(screen.getByRole("heading", { name: "How it works" })).toBeInTheDocument();
  });

  it("renders all three step headings", () => {
    render(<HowItWorks />);
    expect(screen.getByRole("heading", { name: "Smart search" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Choose property" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Reach the broker" })).toBeInTheDocument();
  });

  it("renders step descriptions", () => {
    render(<HowItWorks />);
    expect(screen.getByText(/our app finds you the perfect match/i)).toBeInTheDocument();
  });
});
