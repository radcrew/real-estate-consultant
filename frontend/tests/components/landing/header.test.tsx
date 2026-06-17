// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Header } from "@components/landing/header";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

vi.mock("@headlessui/react", () => ({
  Popover: ({ children }: { children: React.ReactNode }) => <li>{children}</li>,
  PopoverButton: ({ children }: { children: React.ReactNode }) => <button>{children}</button>,
  PopoverPanel: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Dialog: ({ children, open }: { children: React.ReactNode; open: boolean }) =>
    open ? <div>{children}</div> : null,
  DialogBackdrop: () => null,
  DialogPanel: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@contexts/auth", () => ({
  useAuth: () => ({ session: null, ready: true }),
}));

vi.mock("@components/ui/nav-mobile", () => ({
  NavMobile: () => <div data-testid="nav-mobile" />,
}));

describe("Header", () => {
  it("renders the brand logo", () => {
    render(<Header />);
    expect(screen.getByText("RadEstate")).toBeInTheDocument();
  });

  it("renders the list-your-property link", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: /list your property/i })).toHaveAttribute(
      "href",
      "/list-property",
    );
  });

  it("renders sign-in and get-started links when signed out", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: "Sign In" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Get Started" })).toBeInTheDocument();
  });

  it("renders inside a header landmark", () => {
    render(<Header />);
    expect(screen.getByRole("banner")).toBeInTheDocument();
  });
});
