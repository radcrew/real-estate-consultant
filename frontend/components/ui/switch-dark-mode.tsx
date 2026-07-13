"use client";

import { Moon, Sun } from "lucide-react";

import { useThemeMode } from "@hooks/use-theme-mode";
import { cn } from "@utils/common";

/**
 * Voyager-styled light/dark toggle button.
 *
 * Ported from Voyager's `shared/SwitchDarkMode.tsx`; Heroicons swapped for
 * lucide `Moon`/`Sun`, and the theme state comes from the dependency-free
 * `useThemeMode` hook.
 */
export interface SwitchDarkModeProps {
  className?: string;
}

export const SwitchDarkMode = ({ className }: SwitchDarkModeProps) => {
  const { isDarkMode, toggleDarkMode } = useThemeMode();

  return (
    <button
      type="button"
      onClick={toggleDarkMode}
      className={cn(
        "flex h-12 w-12 items-center justify-center self-center rounded-full text-neutral-700 hover:bg-neutral-100 focus:outline-none",
        "dark:text-neutral-300 dark:hover:bg-neutral-800",
        className,
      )}
    >
      <span className="sr-only">Enable dark mode</span>
      {isDarkMode ? (
        <Moon className="h-7 w-7" aria-hidden />
      ) : (
        <Sun className="h-7 w-7" aria-hidden />
      )}
    </button>
  );
};

