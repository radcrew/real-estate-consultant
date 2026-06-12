import { cn } from "@utils/common";

/**
 * Voyager `BgGlassmorphism` — soft blurred color blobs behind hero sections.
 * Ported verbatim except the colors use RadEstate's indigo + teal accents.
 */
type BgGlassmorphismProps = {
  className?: string;
};

export const BgGlassmorphism = ({
  className = "absolute inset-x-0 z-0 flex min-h-0 overflow-hidden py-24 pl-20 md:top-10 xl:top-40",
}: BgGlassmorphismProps) => (
  <div className={cn("pointer-events-none", className)} aria-hidden>
    <span className="block size-72 rounded-full bg-[#6366f1] opacity-10 mix-blend-multiply blur-3xl lg:size-96" />
    <span className="-ml-20 mt-40 block size-72 rounded-full bg-[#14b8a6] opacity-10 mix-blend-multiply blur-3xl lg:size-96" />
  </div>
);
