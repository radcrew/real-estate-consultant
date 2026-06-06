"use client";

import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@utils/common";

/**
 * Voyager-styled primary button (pill shape, indigo).
 *
 * Ported from Voyager's `shared/Button.tsx` + `shared/ButtonPrimary.tsx`,
 * adapted to this stack: `cn()` instead of template strings, `string` hrefs
 * (typedRoutes is off here), React 19 conventions, and the `primary-*` tokens
 * added in globals.css. Voyager's `bg-primary-6000` typo is corrected to
 * `bg-primary-600`. Kept separate from the existing shadcn `Button` so neither
 * design system disturbs the other.
 */
export interface ButtonPrimaryProps {
  className?: string;
  sizeClass?: string;
  fontSize?: string;
  loading?: boolean;
  disabled?: boolean;
  type?: ButtonHTMLAttributes<HTMLButtonElement>["type"];
  href?: string;
  targetBlank?: boolean;
  onClick?: () => void;
  children?: ReactNode;
}

const Spinner = () => (
  <svg
    className="-ml-1 mr-3 h-5 w-5 animate-spin"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="3"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
);

export const ButtonPrimary = ({
  className = "",
  sizeClass = "px-4 py-3 sm:px-6",
  fontSize = "text-sm sm:text-base font-medium",
  loading = false,
  disabled = false,
  type,
  href,
  targetBlank,
  onClick,
  children,
}: ButtonPrimaryProps) => {
  const classes = cn(
    "relative inline-flex h-auto items-center justify-center rounded-full transition-colors",
    "bg-primary-600 text-neutral-50 hover:bg-primary-700 disabled:opacity-70",
    fontSize,
    sizeClass,
    className,
  );

  if (href) {
    return (
      <Link
        href={href}
        target={targetBlank ? "_blank" : undefined}
        rel={targetBlank ? "noopener noreferrer" : undefined}
        className={classes}
        onClick={onClick}
      >
        {children}
      </Link>
    );
  }

  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={classes}
      onClick={onClick}
    >
      {loading && <Spinner />}
      {children}
    </button>
  );
};

export default ButtonPrimary;
