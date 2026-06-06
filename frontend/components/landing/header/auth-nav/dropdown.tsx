"use client";

import { LogOut, UserRound } from "lucide-react";
import { useRouter } from "next/navigation";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@components/ui/dropdown-menu";
import { Avatar } from "@components/ui/voyager/avatar";
import { useAuth } from "@contexts/auth";

export const ProfileDropdown = () => {
  const router = useRouter();
  const { session, signOut } = useAuth();
  if (!session) {
    return null;
  }

  const label = session.user.email?.trim() || "Account";
  const avatarUrl = session.user.avatarUrl?.trim();

  return (
    <DropdownMenu modal={false}>

      <DropdownMenuTrigger
        aria-label="Account menu"
        className="shrink-0 rounded-full outline-none focus-visible:outline-none"
      >
        <Avatar
          imgUrl={avatarUrl || undefined}
          userName={label}
          sizeClass="h-9 w-9 text-base"
          containerClassName="ring-1 ring-neutral-200 dark:ring-neutral-700"
          unoptimized
          referrerPolicy="no-referrer"
        />
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" side="bottom" sideOffset={8} className="min-w-48">

        <DropdownMenuGroup>
          <DropdownMenuLabel className="max-w-64 truncate text-sm font-normal text-foreground">
            {label}
          </DropdownMenuLabel>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        <DropdownMenuGroup>
          <DropdownMenuItem onClick={() => router.push("/account")}>
            <UserRound className="size-4" />
            Account
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        <DropdownMenuGroup>
          <DropdownMenuItem onClick={signOut}>
            <LogOut className="size-4" />
            Sign out
          </DropdownMenuItem>
        </DropdownMenuGroup>

      </DropdownMenuContent>

    </DropdownMenu>
  );
};
