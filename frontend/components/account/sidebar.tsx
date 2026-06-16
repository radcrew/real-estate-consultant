"use client";

import Link from "next/link";
import { Building2, Heart, KeyRound, UserCircle } from "lucide-react";

import { Avatar } from "@components/ui/avatar";
import { brand } from "@config/brand";
import { useAuth } from "@contexts/auth";
import { cn } from "@utils/common";

/**
 * Voyager `AccountSidebar` adapted to this app: dark workspace rail with the
 * brand block, the signed-in user's avatar, and a tabbed nav for the account
 * sections. Profile + Security are in-page tabs (switch the visible panel);
 * Saved is a real route since it lives on its own page.
 */
export type AccountTab = "profile" | "security";

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
];

const ITEM_CLASS =
  "group flex flex-shrink-0 items-center gap-3 rounded-lg border-l-2 px-3 py-3 text-left transition-colors";
const DESCRIPTION = "hidden text-xs text-neutral-500 group-hover:text-neutral-400 lg:block";

type AccountSidebarProps = {
  activeTab: AccountTab;
  onSelectTab: (tab: AccountTab) => void;
};

export const AccountSidebar = ({ activeTab, onSelectTab }: AccountSidebarProps) => {
  const { session } = useAuth();
  const email = session?.user.email?.trim() ?? "";
  const avatarUrl = session?.user.avatarUrl?.trim() || undefined;

  return (
    <aside className="flex-shrink-0 bg-neutral-950 text-neutral-200 lg:min-h-[calc(100vh-5rem)] lg:w-72">
      <div className="border-b border-neutral-800 px-6 pb-6 pt-8">
        <Link href="/" className="inline-flex items-center gap-2">
          <span className="flex size-9 items-center justify-center rounded-lg bg-primary-600 text-white">
            <Building2 className="size-5" aria-hidden />
          </span>
          <span className="text-lg font-semibold text-white">{brand.name}</span>
        </Link>
        <p className="mt-2 text-xs text-neutral-500">{brand.tagline}</p>
      </div>

      <div className="hidden border-b border-neutral-800 px-6 py-6 lg:block">
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
            <p className="truncate font-medium text-white">{email || "Your account"}</p>
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
              className={cn(
                ITEM_CLASS,
                active
                  ? "border-primary-500 bg-neutral-900 text-white"
                  : "border-transparent text-neutral-400 hover:bg-neutral-900 hover:text-neutral-100",
              )}
            >
              <Icon
                className={cn(
                  "size-5 flex-shrink-0",
                  active ? "text-primary-400" : "text-neutral-500 group-hover:text-primary-400",
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

        <Link
          href="/saved"
          className={cn(ITEM_CLASS, "border-transparent text-neutral-400 hover:bg-neutral-900 hover:text-neutral-100")}
        >
          <Heart
            className="size-5 flex-shrink-0 text-neutral-500 group-hover:text-primary-400"
            aria-hidden
          />
          <span className="min-w-0">
            <span className="block text-sm font-medium">Saved</span>
            <span className={DESCRIPTION}>
              Properties you&rsquo;ve saved
            </span>
          </span>
        </Link>
      </nav>
    </aside>
  );
};
