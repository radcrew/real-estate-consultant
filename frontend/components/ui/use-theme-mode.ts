"use client";

import { useCallback, useEffect, useSyncExternalStore } from "react";

/**
 * Dark-mode hook ported from Voyager's `utils/useThemeMode.ts`.
 *
 * Voyager used `react-hooks-global-state` to share the flag; this self-contained
 * version drops that dependency. The preference lives in `localStorage.theme`,
 * read via `useSyncExternalStore` (SSR-safe: the server snapshot is light), and
 * an effect mirrors it onto the `.dark` class on <html> that globals.css keys
 * off. Note: like Voyager, the class is applied in an effect, so there may be a
 * brief flash before hydration — an anti-FOUC <head> script can be added later.
 */
const themeListeners = new Set<() => void>();

const subscribe = (callback: () => void) => {
  themeListeners.add(callback);
  window.addEventListener("storage", callback);
  return () => {
    themeListeners.delete(callback);
    window.removeEventListener("storage", callback);
  };
};

const isDark = () => localStorage.theme === "dark";

const setTheme = (dark: boolean) => {
  localStorage.theme = dark ? "dark" : "light";
  themeListeners.forEach((listener) => listener());
};

export const useThemeMode = () => {
  const isDarkMode = useSyncExternalStore(subscribe, isDark, () => false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDarkMode);
  }, [isDarkMode]);

  const toDark = useCallback(() => setTheme(true), []);
  const toLight = useCallback(() => setTheme(false), []);
  const toggleDarkMode = useCallback(() => setTheme(!isDark()), []);

  return { isDarkMode, toDark, toLight, toggleDarkMode };
};
