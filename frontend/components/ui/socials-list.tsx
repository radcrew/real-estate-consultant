import type { ReactNode } from "react";

import { cn } from "@utils/common";

/**
 * Voyager-styled social links list.
 *
 * Consolidates Voyager's `SocialsList` (icon-only row) and `SocialsList1`
 * (icon + name, used in footers) via the `showNames` prop. Voyager used
 * line-awesome brand icons; lucide has no brand icons, so the defaults are
 * inline SVG glyphs. Consumers can pass their own `icon: ReactNode`.
 */
export interface SocialItem {
  name: string;
  href: string;
  icon: ReactNode;
}

export interface SocialsListProps {
  className?: string;
  itemClass?: string;
  socials?: SocialItem[];
  showNames?: boolean;
}

const BrandSvg = ({ children }: { children: ReactNode }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="h-6 w-6" aria-hidden>
    {children}
  </svg>
);

const DEFAULT_SOCIALS: SocialItem[] = [
  {
    name: "Facebook",
    href: "https://meta.com/radestate",
    icon: (
      <BrandSvg>
        <path d="M22 12.06C22 6.5 17.52 2 12 2S2 6.5 2 12.06c0 5 3.66 9.15 8.44 9.94v-7.03H7.9v-2.9h2.54V9.85c0-2.51 1.49-3.9 3.78-3.9 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.78-1.63 1.57v1.88h2.78l-.44 2.9h-2.34V22c4.78-.79 8.44-4.94 8.44-9.94Z" />
      </BrandSvg>
    ),
  },
  {
    name: "Twitter",
    href: "https://x.com/radestate",
    icon: (
      <BrandSvg>
        <path d="M18.9 2H22l-7.5 8.6L23 22h-6.6l-5.2-6.8L5.3 22H2l8-9.2L1.5 2h6.8l4.7 6.2L18.9 2Zm-1.2 18h1.8L7.2 3.9H5.3L17.7 20Z" />
      </BrandSvg>
    ),
  },
  {
    name: "Youtube",
    href: "https://youtube.com/radestate",
    icon: (
      <BrandSvg>
        <path d="M23 7.5a3 3 0 0 0-2.1-2.1C19 4.9 12 4.9 12 4.9s-7 0-8.9.5A3 3 0 0 0 1 7.5 31 31 0 0 0 .5 12 31 31 0 0 0 1 16.5a3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 23.5 12 31 31 0 0 0 23 7.5ZM9.8 15.3V8.7l5.7 3.3-5.7 3.3Z" />
      </BrandSvg>
    ),
  },
  {
    name: "Instagram",
    href: "https://instagram.com/radestate",
    icon: (
      <BrandSvg>
        <path d="M12 2.2c3.2 0 3.6 0 4.9.07 1.2.06 1.8.26 2.2.43.6.2 1 .47 1.4.9.43.4.7.8.9 1.4.17.4.37 1 .43 2.2.07 1.3.07 1.7.07 4.9s0 3.6-.07 4.9c-.06 1.2-.26 1.8-.43 2.2-.2.6-.47 1-.9 1.4-.4.43-.8.7-1.4.9-.4.17-1 .37-2.2.43-1.3.07-1.7.07-4.9.07s-3.6 0-4.9-.07c-1.2-.06-1.8-.26-2.2-.43-.6-.2-1-.47-1.4-.9-.43-.4-.7-.8-.9-1.4-.17-.4-.37-1-.43-2.2C2.2 15.6 2.2 15.2 2.2 12s0-3.6.07-4.9c.06-1.2.26-1.8.43-2.2.2-.6.47-1 .9-1.4.4-.43.8-.7 1.4-.9.4-.17 1-.37 2.2-.43C8.4 2.2 8.8 2.2 12 2.2Zm0 4.9a4.9 4.9 0 1 0 0 9.8 4.9 4.9 0 0 0 0-9.8Zm0 1.8a3.1 3.1 0 1 1 0 6.2 3.1 3.1 0 0 1 0-6.2Zm5.1-2.1a1.15 1.15 0 1 0 0 2.3 1.15 1.15 0 0 0 0-2.3Z" />
      </BrandSvg>
    ),
  },
];

export const SocialsList = ({
  className,
  itemClass = "block",
  socials = DEFAULT_SOCIALS,
  showNames = false,
}: SocialsListProps) => {
  if (showNames) {
    return (
      <div className={cn("space-y-2.5", className)}>
        {socials.map((item, i) => (
          <a
            key={i}
            href={item.href}
            target="_blank"
            rel="noopener noreferrer"
            title={item.name}
            className="group flex items-center space-x-2 leading-none text-neutral-700 hover:text-black dark:text-neutral-300 dark:hover:text-white"
          >
            {item.icon}
            <span className="hidden text-sm lg:block">{item.name}</span>
          </a>
        ))}
      </div>
    );
  }

  return (
    <nav
      className={cn(
        "flex space-x-2.5 text-neutral-600 dark:text-neutral-300",
        className,
      )}
    >
      {socials.map((item, i) => (
        <a
          key={i}
          href={item.href}
          target="_blank"
          rel="noopener noreferrer"
          title={item.name}
          className={itemClass}
        >
          {item.icon}
        </a>
      ))}
    </nav>
  );
};

