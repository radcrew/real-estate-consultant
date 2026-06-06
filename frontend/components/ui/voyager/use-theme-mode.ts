"use client";

import { useCallback, useEffect, useState } from "react";

/**
 * Dark-mode hook ported from Voyager's `utils/useThemeMode.ts`.
 *
 * Voyager used `react-hooks-global-state` to share the flag; this self-contained
 * version drops that dependency. It toggles the `.dark` class on <html> (the
 * variant globals.css keys off) and persists the choice to `localStorage.theme`.
 * Note: like Voyager, the class is applied in an effect, so there may be a brief
 * flash before hydration — an anti-FOUC <head> script can be added later.
 */
export const useThemeMode = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  const toDark = useCallback(() => {
    setIsDarkMode(true);
    document.documentElement.classList.add("dark");
    localStorage.theme = "dark";
  }, []);

  const toLight = useCallback(() => {
    setIsDarkMode(false);
    document.documentElement.classList.remove("dark");
    localStorage.theme = "light";
  }, []);

  useEffect(() => {
    if (localStorage.theme === "dark") {
      toDark();
    } else {
      toLight();
    }
  }, [toDark, toLight]);

  const toggleDarkMode = useCallback(() => {
    if (localStorage.theme === "dark") {
      toLight();
    } else {
      toDark();
    }
  }, [toDark, toLight]);

  return { isDarkMode, toDark, toLight, toggleDarkMode };
};
