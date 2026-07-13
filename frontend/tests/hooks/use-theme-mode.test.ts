// @vitest-environment jsdom
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useThemeMode } from "@hooks/use-theme-mode";

beforeEach(() => {
  localStorage.clear();
  document.documentElement.classList.remove("dark");
});

afterEach(() => {
  localStorage.clear();
  document.documentElement.classList.remove("dark");
});

describe("useThemeMode", () => {
  it("defaults to light mode when localStorage has no theme", () => {
    const { result } = renderHook(() => useThemeMode());
    expect(result.current.isDarkMode).toBe(false);
  });

  it("reads dark mode from localStorage on init", () => {
    localStorage.theme = "dark";
    const { result } = renderHook(() => useThemeMode());
    expect(result.current.isDarkMode).toBe(true);
  });

  it("switches to dark mode with toDark()", () => {
    const { result } = renderHook(() => useThemeMode());
    act(() => result.current.toDark());
    expect(result.current.isDarkMode).toBe(true);
    expect(localStorage.theme).toBe("dark");
  });

  it("switches to light mode with toLight()", () => {
    localStorage.theme = "dark";
    const { result } = renderHook(() => useThemeMode());
    act(() => result.current.toLight());
    expect(result.current.isDarkMode).toBe(false);
    expect(localStorage.theme).toBe("light");
  });

  it("toggles dark mode with toggleDarkMode()", () => {
    const { result } = renderHook(() => useThemeMode());
    act(() => result.current.toggleDarkMode());
    expect(result.current.isDarkMode).toBe(true);
    act(() => result.current.toggleDarkMode());
    expect(result.current.isDarkMode).toBe(false);
  });

  it("applies the dark class to document.documentElement when dark", () => {
    const { result } = renderHook(() => useThemeMode());
    act(() => result.current.toDark());
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("removes the dark class when switching to light", () => {
    localStorage.theme = "dark";
    const { result } = renderHook(() => useThemeMode());
    act(() => result.current.toLight());
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});
