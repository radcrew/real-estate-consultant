"use client";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@components/ui/dropdown-menu";
import { ChevronDown } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@utils/common";

/**
 * Voyager-styled navigation item.
 *
 * Simplified port of Voyager's `shared/Navigation/NavigationItem.tsx`: keeps the
 * pill main-link look and supports a single-level dropdown via Base UI `Menu`.
 * Voyager's mega-menu and multi-level hover dropdowns are omitted (not needed
 * for RadEstate). Heroicons chevron -> lucide.
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

const childLinkClass =
  "flex items-center rounded-md px-4 py-2 font-normal text-neutral-600 hover:bg-neutral-100 hover:text-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800 dark:hover:text-neutral-200";

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
      <li className="menu-item relative flex items-center">
        <DropdownMenu modal={false}>
          <DropdownMenuTrigger
            className={cn(mainLinkClass, "focus:outline-none")}
          >
            {menuItem.name}
            <ChevronDown
              className="-mr-1 ml-1 h-4 w-4 text-neutral-400"
              aria-hidden
            />
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="start"
            side="bottom"
            sideOffset={12}
            className="w-56 p-2"
          >
            <ul className="grid gap-1">
              {menuItem.children.map((child) => (
                <li key={child.id}>
                  <Link
                    href={child.href}
                    target={child.targetBlank ? "_blank" : undefined}
                    rel={child.targetBlank ? "noopener noreferrer" : undefined}
                    className={childLinkClass}
                  >
                    {child.name}
                  </Link>
                </li>
              ))}
            </ul>
          </DropdownMenuContent>
        </DropdownMenu>
      </li>
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
