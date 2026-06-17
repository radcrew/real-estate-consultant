// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { BtnLikeIcon } from "@components/ui/btn-like-icon";

const mockContext = {
  isSaved: vi.fn(() => false),
  toggle: vi.fn(),
  savedIds: [] as string[],
  ready: true,
  signedIn: false,
};

vi.mock("@components/saved/provider", () => ({
  useSavedListings: () => mockContext,
}));

beforeEach(() => {
  mockContext.isSaved = vi.fn(() => false);
  mockContext.toggle = vi.fn();
});

describe("BtnLikeIcon", () => {
  it("renders a Save button", () => {
    render(<BtnLikeIcon />);
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
  });

  it("shows 'Saved' aria-label when liked (local state)", async () => {
    render(<BtnLikeIcon isLiked />);
    expect(screen.getByRole("button", { name: "Saved" })).toBeInTheDocument();
  });

  it("toggles local like state when no id is provided", async () => {
    render(<BtnLikeIcon />);
    const btn = screen.getByRole("button");
    expect(btn).toHaveAttribute("aria-pressed", "false");
    await userEvent.click(btn);
    expect(btn).toHaveAttribute("aria-pressed", "true");
  });

  it("calls context toggle when id is provided", async () => {
    render(<BtnLikeIcon id="listing-1" />);
    await userEvent.click(screen.getByRole("button"));
    expect(mockContext.toggle).toHaveBeenCalledWith("listing-1");
  });

  it("uses isSaved from context when id is provided", () => {
    mockContext.isSaved = vi.fn(() => true);
    render(<BtnLikeIcon id="listing-1" />);
    expect(screen.getByRole("button", { name: "Saved" })).toBeInTheDocument();
  });

  it("stops click propagation", async () => {
    const parentClick = vi.fn();
    render(
      <div onClick={parentClick}>
        <BtnLikeIcon />
      </div>,
    );
    await userEvent.click(screen.getByRole("button"));
    expect(parentClick).not.toHaveBeenCalled();
  });
});
