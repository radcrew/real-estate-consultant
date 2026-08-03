// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AccountSidebar } from "@components/account/sidebar";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

const mockUseAuth = vi.fn();
vi.mock("@contexts/auth", () => ({
  useAuth: () => mockUseAuth(),
}));

beforeEach(() => {
  mockUseAuth.mockReturnValue({ session: { user: { email: "user@test.com", avatarUrl: null } } });
});

describe("AccountSidebar", () => {
  it("renders account navigation", () => {
    render(<AccountSidebar activeTab="profile" onSelectTab={vi.fn()} />);
    expect(screen.getByRole("navigation", { name: /account navigation/i })).toBeInTheDocument();
  });

  it("marks active tab with aria-current", () => {
    render(<AccountSidebar activeTab="profile" onSelectTab={vi.fn()} />);
    expect(screen.getByRole("button", { name: /personal info/i })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("button", { name: /security/i })).not.toHaveAttribute("aria-current");
  });

  it("calls onSelectTab when a tab is clicked", () => {
    const onSelectTab = vi.fn();
    render(<AccountSidebar activeTab="profile" onSelectTab={onSelectTab} />);
    fireEvent.click(screen.getByRole("button", { name: /security/i }));
    expect(onSelectTab).toHaveBeenCalledWith("security");
  });

  it("keeps saved properties in-page so the sidebar survives the click", () => {
    const onSelectTab = vi.fn();
    render(<AccountSidebar activeTab="profile" onSelectTab={onSelectTab} />);
    expect(screen.queryByRole("link", { name: /saved/i })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /saved/i }));
    expect(onSelectTab).toHaveBeenCalledWith("saved");
  });

  it("shows user email when signed in", () => {
    render(<AccountSidebar activeTab="profile" onSelectTab={vi.fn()} />);
    expect(screen.getByText("user@test.com")).toBeInTheDocument();
  });

  // The rail used to hardcode its dark palette, so the header's theme toggle
  // flipped every surface around it and left the sidebar dark.
  it("pairs every rail surface color with a dark: variant", () => {
    const { container } = render(<AccountSidebar activeTab="profile" onSelectTab={vi.fn()} />);
    const surfaces = [
      container.querySelector("aside"),
      ...container.querySelectorAll("nav button"),
    ];

    for (const el of surfaces) {
      const classes = (el?.className ?? "").split(/\s+/);
      // Every base surface property the rail paints must have a dark override,
      // whatever shade that override picks.
      const properties = new Set(
        classes.flatMap((c) => (/^(bg|text)-/.test(c) ? [c.split("-")[0]] : [])),
      );
      expect(properties.size).toBeGreaterThan(0);
      for (const property of properties) {
        expect(classes.some((c) => c.startsWith(`dark:${property}-`))).toBe(true);
      }
    }
  });
});
