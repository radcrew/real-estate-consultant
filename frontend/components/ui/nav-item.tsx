"use client";

import { Popover, PopoverButton, PopoverPanel } from "@headlessui/react";
import { ChevronDown } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@utils/common";

/**
 * Voyager-styled navigation item.
 *
 * Simplified port of Voyager's `shared/Navigation/NavigationItem.tsx`: keeps the
 * pill main-link look and supports a single-level dropdown via Headless UI v2
 * `Popover` (click-based). Voyager's mega-menu and multi-level hover dropdowns
 * are omitted (not needed for RadEstate). Heroicons chevron -> lucide.
 */
export interface NavItemType {
  id: string;
  name: string;
  href: string;
  targetBlank?: boolean;
  children?: NavItemType[];
}

const mainLinkClass =
  "inline-flex items-center rounded-full px-4 py-2 text-sm font-normal text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900 xl:px-5 xl:text-base dark:text-neutral-300 dark:hover:bg-neutral-800 dark:hover:text-neutral-200";

const activeLinkClass =
  "bg-neutral-100 font-medium text-neutral-900 dark:bg-neutral-800 dark:text-neutral-100";

export interface NavigationItemProps {
  menuItem: NavItemType;
}

export const NavigationItem = ({ menuItem }: NavigationItemProps) => {
  const pathname = usePathname();
  const isActive =
    menuItem.href === "/"
      ? pathname === "/"
      : pathname === menuItem.href || pathname.startsWith(`${menuItem.href}/`);

  if (menuItem.children?.length) {
    return (
      <Popover as="li" className="menu-item relative flex items-center">
        <PopoverButton className={cn(mainLinkClass, "focus:outline-none")}>
          {menuItem.name}
          <ChevronDown
            className="-mr-1 ml-1 h-4 w-4 text-neutral-400"
            aria-hidden
          />
        </PopoverButton>
        <PopoverPanel
          transition
          anchor="bottom start"
          className="z-20 mt-3 w-56 rounded-lg bg-white py-4 text-sm shadow-lg ring-1 ring-black/5 transition duration-150 ease-out data-[closed]:translate-y-1 data-[closed]:opacity-0 dark:bg-neutral-900 dark:ring-white/10"
        >
          <ul className="grid gap-1">
            {menuItem.children.map((child) => (
              <li key={child.id} className="px-2">
                <Link
                  href={child.href}
                  target={child.targetBlank ? "_blank" : undefined}
                  rel={child.targetBlank ? "noopener noreferrer" : undefined}
                  className="flex items-center rounded-md px-4 py-2 font-normal text-neutral-600 hover:bg-neutral-100 hover:text-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800 dark:hover:text-neutral-200"
                >
                  {child.name}
                </Link>
              </li>
            ))}
          </ul>
        </PopoverPanel>
      </Popover>
    );
  }

  return (
    <li className="menu-item flex items-center">
      <Link
        href={menuItem.href}
        target={menuItem.targetBlank ? "_blank" : undefined}
        rel={menuItem.targetBlank ? "noopener noreferrer" : undefined}
        aria-current={isActive ? "page" : undefined}
        className={cn(mainLinkClass, isActive && activeLinkClass)}
      >
        {menuItem.name}
      </Link>
    </li>
  );
};

