// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Navigation, DEFAULT_NAV } from "@components/ui/navigation";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

// Headlessui Popover needs a portal target
vi.mock("@headlessui/react", () => ({
  Popover: ({ children }: { children: React.ReactNode }) => <li>{children}</li>,
  PopoverButton: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <button className={className}>{children}</button>
  ),
  PopoverPanel: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe("Navigation", () => {
  it("renders all default nav items", () => {
    render(<Navigation />);
    expect(screen.getByText("Listings")).toBeInTheDocument();
    expect(screen.getByText("Insights")).toBeInTheDocument();
    expect(screen.getByText("About")).toBeInTheDocument();
    expect(screen.getByText("Contact")).toBeInTheDocument();
  });

  it("accepts a custom menu", () => {
    render(
      <Navigation
        menu={[
          { id: "home", name: "Home", href: "/" },
          { id: "faq", name: "FAQ", href: "/faq" },
        ]}
      />,
    );
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("FAQ")).toBeInTheDocument();
  });

  it("DEFAULT_NAV has at least 4 items", () => {
    expect(DEFAULT_NAV.length).toBeGreaterThanOrEqual(4);
  });
});
