// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Footer } from "@components/landing/footer";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@components/ui/socials-list", () => ({
  SocialsList: () => <div data-testid="socials-list" />,
}));

describe("Footer", () => {
  it("renders the brand logo", () => {
    render(<Footer />);
    expect(screen.getByText("RadEstate")).toBeInTheDocument();
  });

  it("renders column headings", () => {
    render(<Footer />);
    expect(screen.getByText("Explore")).toBeInTheDocument();
    expect(screen.getByText("Account")).toBeInTheDocument();
    expect(screen.getByText("Company")).toBeInTheDocument();
  });

  it("renders navigation links", () => {
    render(<Footer />);
    expect(screen.getByRole("link", { name: "Listings" })).toHaveAttribute("href", "/listings");
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/sign-in");
    expect(screen.getByRole("link", { name: "Privacy" })).toHaveAttribute("href", "/privacy");
  });

  it("renders the copyright year", () => {
    render(<Footer />);
    const year = new Date().getFullYear();
    expect(screen.getByText(new RegExp(String(year)))).toBeInTheDocument();
  });
});
