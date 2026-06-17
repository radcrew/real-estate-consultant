// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { NavigationItem } from "@components/ui/nav-item";

vi.mock("next/link", () => ({
  default: ({ href, children, "aria-current": ariaCurrent }: { href: string; children: React.ReactNode; "aria-current"?: string }) => (
    <a href={href} aria-current={ariaCurrent}>{children}</a>
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/listings",
}));

vi.mock("@headlessui/react", () => ({
  Popover: ({ children }: { children: React.ReactNode }) => <li>{children}</li>,
  PopoverButton: ({ children }: { children: React.ReactNode }) => <button>{children}</button>,
  PopoverPanel: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const ITEM = { id: "listings", name: "Listings", href: "/listings" };
const ITEM_HOME = { id: "home", name: "Home", href: "/" };
const ITEM_WITH_CHILDREN = {
  id: "resources",
  name: "Resources",
  href: "/resources",
  children: [
    { id: "blog", name: "Blog", href: "/blog" },
  ],
};

describe("NavigationItem", () => {
  it("renders a link with the item name", () => {
    render(<NavigationItem menuItem={ITEM} />);
    expect(screen.getByRole("link", { name: "Listings" })).toHaveAttribute("href", "/listings");
  });

  it("marks the active page with aria-current", () => {
    render(<NavigationItem menuItem={ITEM} />);
    expect(screen.getByRole("link")).toHaveAttribute("aria-current", "page");
  });

  it("does not mark inactive item with aria-current", () => {
    render(<NavigationItem menuItem={ITEM_HOME} />);
    expect(screen.getByRole("link")).not.toHaveAttribute("aria-current");
  });

  it("renders children as dropdown when item has children", () => {
    render(<NavigationItem menuItem={ITEM_WITH_CHILDREN} />);
    expect(screen.getByRole("button", { name: "Resources" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Blog" })).toHaveAttribute("href", "/blog");
  });
});
