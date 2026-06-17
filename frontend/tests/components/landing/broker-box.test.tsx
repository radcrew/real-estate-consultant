// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BrokerBox } from "@components/landing/author-box";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

describe("BrokerBox", () => {
  it("renders the section heading", () => {
    render(<BrokerBox />);
    expect(screen.getByText(/top brokers this month/i)).toBeInTheDocument();
  });

  it("renders at least one broker card", () => {
    render(<BrokerBox />);
    const headings = screen.getAllByRole("heading");
    expect(headings.length).toBeGreaterThan(0);
  });

  it("applies custom className", () => {
    const { container } = render(<BrokerBox className="mt-20" />);
    expect(container.firstChild).toHaveClass("mt-20");
  });
});
