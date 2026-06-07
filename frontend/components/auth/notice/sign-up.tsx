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
      className="rounded-xl border border-neutral-200 bg-neutral-50 px-4 py-3 text-sm text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-200"
    >
      Account created. Sign in with your email and password.
    </p>
  );
};
