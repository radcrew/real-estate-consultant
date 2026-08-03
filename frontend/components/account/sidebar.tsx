"use client";

import { Heart, KeyRound, Plug, UserCircle } from "lucide-react";

import { Avatar } from "@components/ui/avatar";
import { brand } from "@config/brand";
import { useAuth } from "@contexts/auth";
import { cn } from "@utils/common";

/**
 * Voyager `AccountSidebar` adapted to this app: a workspace rail with the
 * signed-in user's avatar and a tabbed nav for the account sections. Branding
 * is left to the site header above it. Every entry is an in-page tab that
 * swaps the visible panel — Saved included, so the rail survives the click.
 * The standalone `/saved` route still serves the links in the site header.
 *
 * The rail follows the theme toggle rather than staying dark in both: it sits
 * flush against the header, and a permanently-dark rail under a white header
 * read as a rendering bug. Light mode lifts off the white canvas with a
 * neutral-50 surface; the original dark values live on under `dark:`.
 */
export type AccountTab = "profile" | "security" | "api-keys" | "saved";

const TAB_ITEMS: {
  tab: AccountTab;
  label: string;
  description: string;
  icon: typeof UserCircle;
}[] = [
  {
    tab: "profile",
    label: "Personal info",
    description: "Name, contact and address",
    icon: UserCircle,
  },
  {
    tab: "security",
    label: "Security",
    description: "Change your password",
    icon: KeyRound,
  },
  {
    tab: "api-keys",
    label: "API keys",
    description: "Connect AI tools to your account",
    icon: Plug,
  },
  {
    tab: "saved",
    label: "Saved",
    description: "Properties you’ve saved",
    icon: Heart,
  },
];

const ITEM_CLASS =
  "group flex flex-shrink-0 items-center gap-3 rounded-lg border-l-2 px-3 py-3 text-left transition-colors";
const DESCRIPTION = cn(
  "hidden text-xs text-neutral-500 group-hover:text-neutral-600 lg:block",
  "dark:group-hover:text-neutral-400",
);

const ITEM_ACTIVE = cn(
  "border-primary-500 bg-neutral-100 text-neutral-900",
  "dark:bg-neutral-900 dark:text-white",
);
const ITEM_INACTIVE = cn(
  "border-transparent text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900",
  "dark:text-neutral-400 dark:hover:bg-neutral-900 dark:hover:text-neutral-100",
);

type AccountSidebarProps = {
  activeTab: AccountTab;
  onSelectTab: (tab: AccountTab) => void;
};

export const AccountSidebar = ({ activeTab, onSelectTab }: AccountSidebarProps) => {
  const { session } = useAuth();
  const email = session?.user.email?.trim() ?? "";
  const avatarUrl = session?.user.avatarUrl?.trim() || undefined;

  return (
    <aside
      className={cn(
        "flex-shrink-0 border-neutral-200 bg-neutral-50 text-neutral-700 lg:min-h-[calc(100vh-5rem)] lg:w-72 lg:border-r",
        "dark:border-neutral-800 dark:bg-neutral-950 dark:text-neutral-200",
      )}
    >
      <div className="hidden border-b border-neutral-200 px-6 py-6 lg:block dark:border-neutral-800">
        <div className="flex items-center gap-3">
          <Avatar
            sizeClass="w-11 h-11"
            imgUrl={avatarUrl}
            userName={email || "User"}
            containerClassName="ring-2 ring-primary-500/40"
            sizes="44px"
            unoptimized
          />
          <div className="min-w-0">
            <p className="truncate font-medium text-neutral-900 dark:text-white">
              {email || "Your account"}
            </p>
            <p className="truncate text-xs text-neutral-500">{brand.account.workspaceLabel}</p>
          </div>
        </div>
      </div>

      <nav
        className="flex gap-1 overflow-x-auto px-4 py-5 lg:flex-col lg:overflow-visible"
        aria-label="Account navigation"
      >
        {TAB_ITEMS.map(({ tab, label, description, icon: Icon }) => {
          const active = tab === activeTab;
          return (
            <button
              key={tab}
              type="button"
              onClick={() => onSelectTab(tab)}
              aria-current={active ? "page" : undefined}
              className={cn(ITEM_CLASS, active ? ITEM_ACTIVE : ITEM_INACTIVE)}
            >
              <Icon
                className={cn(
                  "size-5 flex-shrink-0",
                  active
                    ? "text-primary-600 dark:text-primary-400"
                    : "text-neutral-400 group-hover:text-primary-600 dark:text-neutral-500 dark:group-hover:text-primary-400",
                )}
                aria-hidden
              />
              <span className="min-w-0">
                <span className="block text-sm font-medium">{label}</span>
                <span className={DESCRIPTION}>
                  {description}
                </span>
              </span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
};
