// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { HistoryBackButton } from "@components/ui/button-back";

const mockBack = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ back: mockBack }),
}));

describe("HistoryBackButton", () => {
  it("renders a button with default label 'Back'", () => {
    render(<HistoryBackButton />);
    expect(screen.getByRole("button", { name: /back/i })).toBeInTheDocument();
  });

  it("renders a custom label", () => {
    render(<HistoryBackButton>Go back</HistoryBackButton>);
    expect(screen.getByRole("button", { name: /go back/i })).toBeInTheDocument();
  });

  it("calls router.back() when clicked", async () => {
    render(<HistoryBackButton />);
    await userEvent.click(screen.getByRole("button"));
    expect(mockBack).toHaveBeenCalledOnce();
  });
});
