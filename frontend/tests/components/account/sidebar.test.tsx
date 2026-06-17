// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AccountSidebar } from "@components/account/sidebar";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

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

  it("renders the saved properties link", () => {
    render(<AccountSidebar activeTab="profile" onSelectTab={vi.fn()} />);
    expect(screen.getByRole("link", { name: /saved/i })).toHaveAttribute("href", "/saved");
  });

  it("shows user email when signed in", () => {
    render(<AccountSidebar activeTab="profile" onSelectTab={vi.fn()} />);
    expect(screen.getByText("user@test.com")).toBeInTheDocument();
  });
});
