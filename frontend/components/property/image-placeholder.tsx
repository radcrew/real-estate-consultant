import { cn } from "@utils/common";

interface ImagePlaceholderProps {
  label?: string;
  className?: string;
}

/**
 * Soft gradient placeholder shown while a property image is unavailable or loading.
 * Displays the property name centered over a neutral gradient background.
 */
export const ImagePlaceholder = ({ label, className }: ImagePlaceholderProps) => (
  <div
    className={cn(
      "absolute inset-0 flex items-center justify-center bg-gradient-to-br from-neutral-100 to-neutral-200 dark:from-neutral-800 dark:to-neutral-700",
      className,
    )}
  >
    {label && (
      <span className="px-6 text-center text-base font-semibold text-neutral-500 dark:text-neutral-400 line-clamp-3 leading-snug">
        {label}
      </span>
    )}
  </div>
);
