"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { readSession, type StoredSession } from "@lib/auth-session";

import { SignedInNav } from "./signed-in-nav";
import { SignedOutNav } from "./signed-out-nav";

export const AuthNav = () => {
  const pathname = usePathname();
  const [session, setSession] = useState<StoredSession | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- mirror sessionStorage when route changes
    setSession(readSession());
  }, [pathname]);

  return session ? <SignedInNav session={session} /> : <SignedOutNav />;
};
