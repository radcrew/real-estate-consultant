// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SavedView } from "@components/saved/view";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

const mockUseSaved = vi.fn();
vi.mock("@components/saved/provider", () => ({
  useSavedListings: () => mockUseSaved(),
}));

vi.mock("@services/listings", () => ({
  listingsService: { getListing: vi.fn() },
}));

describe("SavedView", () => {
  it("shows sign-in prompt when not signed in and ready", () => {
    mockUseSaved.mockReturnValue({ savedIds: [], isSaved: () => false, ready: true, signedIn: false });
    render(<SavedView />);
    expect(screen.getByText(/sign in to view and save/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /sign in/i })).toHaveAttribute("href", "/sign-in");
  });

  it("shows loading skeletons when signed in but not ready", () => {
    mockUseSaved.mockReturnValue({ savedIds: [], isSaved: () => false, ready: false, signedIn: true });
    render(<SavedView />);
    expect(screen.getByRole("status", { name: /loading saved/i })).toBeInTheDocument();
  });

  it("shows empty-state notice when signed in with no saved properties", () => {
    mockUseSaved.mockReturnValue({ savedIds: [], isSaved: () => false, ready: true, signedIn: true });
    render(<SavedView />);
    expect(screen.getByText(/haven.*t saved any/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /browse properties/i })).toHaveAttribute("href", "/listings");
  });

  it("renders heading", () => {
    mockUseSaved.mockReturnValue({ savedIds: [], isSaved: () => false, ready: true, signedIn: false });
    render(<SavedView />);
    expect(screen.getByRole("heading", { name: /saved properties/i })).toBeInTheDocument();
  });
});
