"use client";

import Image from "next/image";
import { LogOut } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@components/ui/dropdown-menu";
import { useAuth } from "@contexts/auth";
import { cn } from "@lib/utils";

const DEFAULT_AVATAR = "/icons/avatar-default.svg";

const triggerClassName = cn(
  "flex size-8 shrink-0 items-center justify-center rounded-full p-0",
  "outline-none focus-visible:outline-none",
);

export const SignedInNav = () => {
  const { session, signOut } = useAuth();
  if (!session) {
    return null;
  }

  const label = session.user.email?.trim() || "Account";
  const avatarUrl = session.user.avatarUrl?.trim();
  const src = avatarUrl && avatarUrl.length > 0 ? avatarUrl : DEFAULT_AVATAR;

  return (
    <DropdownMenu modal={false}>

      <DropdownMenuTrigger
        aria-label="Account menu"
        className={triggerClassName}
      >
        <Image
          src={src}
          alt=""
          width={32}
          height={32}
          unoptimized
          className="size-8 rounded-full object-cover"
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
          <DropdownMenuItem onClick={signOut}>
            <LogOut className="size-4" />
            Sign out
          </DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>

    </DropdownMenu>
  );
};
