// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { SwitchDarkMode } from "@components/ui/switch-dark-mode";

beforeEach(() => {
  localStorage.clear();
  document.documentElement.classList.remove("dark");
});

afterEach(() => {
  localStorage.clear();
  document.documentElement.classList.remove("dark");
});

describe("SwitchDarkMode", () => {
  it("renders a button", () => {
    render(<SwitchDarkMode />);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("toggles to dark mode when clicked in light mode", async () => {
    render(<SwitchDarkMode />);
    await userEvent.click(screen.getByRole("button"));
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("toggles back to light mode when clicked in dark mode", async () => {
    localStorage.theme = "dark";
    render(<SwitchDarkMode />);
    await userEvent.click(screen.getByRole("button"));
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("applies custom className", () => {
    render(<SwitchDarkMode className="absolute top-2" />);
    expect(screen.getByRole("button")).toHaveClass("absolute", "top-2");
  });
});
