"use client";

import { useSearchParams } from "next/navigation";

export const SignUpNotice = () => {
  const searchParams = useSearchParams();
  if (searchParams.get("registered") !== "1") {
    return null;
  }

  return (
    <p
      role="status"
      className="rounded-none border border-border bg-muted px-3 py-2 text-sm text-foreground"
    >
      Account created. Sign in with your email and password.
    </p>
  );
};
