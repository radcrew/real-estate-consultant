// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { MenuBar } from "@components/ui/menu-bar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

vi.mock("@components/ui/nav-mobile", () => ({
  NavMobile: () => <div data-testid="nav-mobile" />,
}));

describe("MenuBar", () => {
  it("renders a menu button", () => {
    render(<MenuBar />);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("opens the mobile nav drawer when clicked", async () => {
    render(<MenuBar />);
    await userEvent.click(screen.getByRole("button"));
    expect(screen.getByTestId("nav-mobile")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(<MenuBar className="text-white" />);
    expect(screen.getByRole("button")).toHaveClass("text-white");
  });
});
