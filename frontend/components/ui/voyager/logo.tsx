import Link from "next/link";
import { Building2 } from "lucide-react";

import { cn } from "@utils/common";

/**
 * Brand logo, structured like Voyager's `shared/Logo.tsx` (link to "/", a clean
 * focus state) but keeping RadEstate's identity (Building2 + name) instead of
 * Voyager's template SVGs. Uses Voyager's indigo accent (`primary-600`); swap to
 * `text-primary` if RadEstate's amber brand color is preferred.
 */
export interface LogoProps {
  className?: string;
}

export const Logo = ({ className }: LogoProps) => (
  <Link
    href="/"
    className={cn(
      "inline-flex items-center gap-2 text-lg font-bold text-primary-600 focus:outline-none",
      className,
    )}
  >
    <Building2 className="size-6 shrink-0" aria-hidden />
    <span>RadEstate</span>
  </Link>
);

export default Logo;
