// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AuthPageFooter } from "@components/auth/main/footer";
import { AuthPageTitle } from "@components/auth/main/title";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("AuthPageTitle", () => {
  it("renders the title heading", () => {
    render(<AuthPageTitle title="Sign In" description="Welcome back" />);
    expect(screen.getByRole("heading", { name: "Sign In" })).toBeInTheDocument();
  });

  it("renders the description", () => {
    render(<AuthPageTitle title="Sign In" description="Welcome back" />);
    expect(screen.getByText("Welcome back")).toBeInTheDocument();
  });
});

describe("AuthPageFooter", () => {
  it("renders the prompt text", () => {
    render(<AuthPageFooter prompt="No account?" linkHref="/sign-up" linkLabel="Sign up" />);
    expect(screen.getByText("No account?")).toBeInTheDocument();
  });

  it("renders the link", () => {
    render(<AuthPageFooter prompt="No account?" linkHref="/sign-up" linkLabel="Sign up" />);
    expect(screen.getByRole("link", { name: "Sign up" })).toHaveAttribute("href", "/sign-up");
  });
});
