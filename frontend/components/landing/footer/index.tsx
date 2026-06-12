import Link from "next/link";

import { Logo } from "@components/ui/logo";
import { SocialsList } from "@components/ui/socials-list";
import { brand } from "@config/brand";

/**
 * Site footer in Voyager's multi-column layout (logo + socials block plus link
 * columns), adapted from Voyager's `components/Footer.tsx`. Voyager's demo
 * widget links are replaced with RadEstate's real routes, the `neutral-6000`
 * typo is fixed, and the original copyright line is kept. Voyager's mobile
 * sticky FooterNav is intentionally omitted.
 */
interface FooterColumn {
  id: string;
  title: string;
  items: { label: string; href: string }[];
}

const FOOTER_COLUMNS: FooterColumn[] = [
  {
    id: "explore",
    title: "Explore",
    items: [
      { label: "Home", href: "/" },
      { label: "Listings", href: "/listings" },
      { label: "Insights", href: "/blog" },
      { label: "List your property", href: "/list-property" },
      { label: "Contact", href: "/contact" },
    ],
  },
  {
    id: "account",
    title: "Account",
    items: [
      { label: "Sign in", href: "/sign-in" },
      { label: "Get started", href: "/sign-up" },
      { label: "Your account", href: "/account" },
      { label: "Saved", href: "/saved" },
    ],
  },
  {
    id: "company",
    title: "Company",
    items: [
      { label: "About", href: "/about" },
      { label: "Privacy", href: "/privacy" },
      { label: "Terms", href: "/terms" },
    ],
  },
];

export const Footer = () => {
  const year = new Date().getFullYear();

  return (
    <footer className="relative border-t border-neutral-200 py-20 lg:py-24 dark:border-neutral-700">
      <div className="mx-auto max-w-screen-xl px-4">
        <div className="grid grid-cols-2 gap-x-5 gap-y-10 sm:gap-x-8 md:grid-cols-4 lg:gap-x-10">
          <div className="col-span-2 flex flex-col gap-5 md:col-span-4 lg:col-span-1">
            <Logo />
            <p className="max-w-xs text-sm text-neutral-500 dark:text-neutral-400">
              {brand.tagline}
            </p>
            <SocialsList
              showNames
              className="flex items-center space-x-3 lg:flex-col lg:items-start lg:space-y-2.5 lg:space-x-0"
            />
          </div>

          {FOOTER_COLUMNS.map((column) => (
            <div key={column.id} className="text-sm">
              <h2 className="font-semibold text-neutral-700 dark:text-neutral-200">
                {column.title}
              </h2>
              <ul className="mt-5 space-y-4">
                {column.items.map((item) => (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      className="text-neutral-600 hover:text-black dark:text-neutral-300 dark:hover:text-white"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-16 border-t border-neutral-200 pt-8 text-sm text-neutral-500 dark:border-neutral-700 dark:text-neutral-400">
          RadEstate © {year} — Built by RadCrew
        </div>
      </div>
    </footer>
  );
};
