"use client";

import Link from "next/link";
import { Building2, KeyRound, UserCircle } from "lucide-react";

import { Avatar } from "@components/ui/voyager/avatar";
import { brand } from "@config/brand";
import { useAuth } from "@contexts/auth";

/**
 * Voyager `AccountSidebar` adapted to this app: dark workspace rail with the
 * brand block, the signed-in user's avatar, and nav to the account sections.
 * Only Profile + Security exist here (no saved-lists/billing backend), so nav
 * items are in-page anchors rather than separate routes.
 */
const NAV_ITEMS = [
  {
    href: "#profile",
    label: "Personal info",
    description: "Name, contact and address",
    icon: UserCircle,
  },
  {
    href: "#security",
    label: "Security",
    description: "Change your password",
    icon: KeyRound,
  },
] as const;

export const AccountSidebar = () => {
  const { session } = useAuth();
  const email = session?.user.email?.trim() ?? "";

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
            userName={email || "User"}
            containerClassName="ring-2 ring-primary-500/40"
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
        {NAV_ITEMS.map(({ href, label, description, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className="group flex flex-shrink-0 items-center gap-3 rounded-lg border-l-2 border-transparent px-3 py-3 text-neutral-400 transition-colors hover:bg-neutral-900 hover:text-neutral-100"
          >
            <Icon className="size-5 flex-shrink-0 text-neutral-500 group-hover:text-primary-400" aria-hidden />
            <span className="min-w-0">
              <span className="block text-sm font-medium">{label}</span>
              <span className="hidden text-xs text-neutral-500 group-hover:text-neutral-400 lg:block">
                {description}
              </span>
            </span>
          </Link>
        ))}
      </nav>
    </aside>
  );
};
