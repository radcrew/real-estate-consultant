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
      "flex h-full w-full items-center justify-center bg-gradient-to-br from-neutral-100 to-neutral-200 dark:from-neutral-800 dark:to-neutral-700",
      className,
    )}
  >
    {label && (
      <span className="px-4 text-center text-sm font-medium text-neutral-400 dark:text-neutral-500 line-clamp-3">
        {label}
      </span>
    )}
  </div>
);
