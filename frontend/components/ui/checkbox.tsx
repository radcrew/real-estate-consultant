"use client";

import { cn } from "@utils/common";

/**
 * Voyager-styled checkbox with optional label/sub-label.
 *
 * Ported from Voyager's `shared/Checkbox.tsx`. Adapted to this stack: `cn()`,
 * and dropped two classes that don't exist here — `focus:ring-action-primary`
 * (undefined color) and `border-primary` (would resolve to shadcn's amber, not
 * Voyager's intent). The `text-primary-500` accent reads best with the
 * @tailwindcss/forms plugin.
 */
export interface CheckboxProps {
  label?: string;
  subLabel?: string;
  className?: string;
  name: string;
  defaultChecked?: boolean;
  onChange?: (checked: boolean) => void;
}

export const Checkbox = ({
  label,
  subLabel,
  name,
  className,
  defaultChecked,
  onChange,
}: CheckboxProps) => (
  <div className={cn("flex text-sm sm:text-base", className)}>
    <input
      id={name}
      name={name}
      type="checkbox"
      defaultChecked={defaultChecked}
      onChange={(e) => onChange?.(e.target.checked)}
      className={cn(
        "h-6 w-6 rounded border-neutral-500 bg-white text-primary-500",
        "checked:border-primary-500 checked:bg-primary-500",
        "focus:ring-primary-500 dark:bg-neutral-700 dark:checked:bg-primary-500",
      )}
    />
    {label && (
      <label
        htmlFor={name}
        className="ml-3.5 flex flex-1 flex-col justify-center"
      >
        <span className="text-neutral-900 dark:text-neutral-100">{label}</span>
        {subLabel && (
          <p className="mt-1 text-sm font-light text-neutral-500 dark:text-neutral-400">
            {subLabel}
          </p>
        )}
      </label>
    )}
  </div>
);

