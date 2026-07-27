// @vitest-environment jsdom
import { act, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Footer } from "@components/landing/footer";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@components/ui/logo", () => ({
  Logo: () => <span>RadEstate</span>,
}));

vi.mock("@components/ui/socials-list", () => ({
  SocialsList: () => <div data-testid="socials-list" />,
}));

async function renderFooter() {
  await act(async () => {
    render(<Footer />);
  });
}

describe("Footer", () => {
  it("renders the brand logo", async () => {
    await renderFooter();
    expect(screen.getByText("RadEstate")).toBeInTheDocument();
  });

  it("renders column headings", async () => {
    await renderFooter();
    expect(screen.getByText("Explore")).toBeInTheDocument();
    expect(screen.getByText("Company")).toBeInTheDocument();
    expect(screen.queryByText("Account")).not.toBeInTheDocument();
  });

  it("renders navigation links", async () => {
    await renderFooter();
    expect(screen.getByRole("link", { name: "Listings" })).toHaveAttribute("href", "/listings");
    expect(screen.getByRole("link", { name: "About" })).toHaveAttribute("href", "/about");
    expect(screen.getByRole("link", { name: "Privacy" })).toHaveAttribute("href", "/privacy");
    expect(screen.queryByRole("link", { name: "Sign in" })).not.toBeInTheDocument();
  });

  it("renders the copyright year", async () => {
    await renderFooter();
    const year = new Date().getFullYear();
    expect(screen.getByText(new RegExp(String(year)))).toBeInTheDocument();
  });
});
