"use client";

import { useAuth } from "@contexts/auth";

import { SignedInNav } from "./signed-in-nav";
import { SignedOutNav } from "./signed-out-nav";

const AuthNavSkeleton = () => (
  <div
    className="flex items-center gap-3 sm:gap-4"
    aria-busy="true"
    aria-label="Loading account"
  >
    <div className="h-4 w-14 shrink-0 animate-pulse rounded-sm bg-muted" />
    <div className="h-8 w-[5.5rem] shrink-0 animate-pulse rounded-sm bg-muted sm:w-24" />
  </div>
);

export const AuthNav = () => {
  const { session, ready } = useAuth();

  if (!ready) {
    return <AuthNavSkeleton />;
  }

  return session ? <SignedInNav /> : <SignedOutNav />;
};
