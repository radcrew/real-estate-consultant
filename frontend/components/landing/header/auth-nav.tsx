"use client";

import { useAuth } from "@contexts/auth";

import { SignedInNav } from "./signed-in-nav";
import { SignedOutNav } from "./signed-out-nav";

export const AuthNav = () => {
  const { session } = useAuth();

  return session ? <SignedInNav session={session} /> : <SignedOutNav />;
};
