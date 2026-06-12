"use client";

import { useSearchParams } from "next/navigation";

export const OAuthErrorNotice = () => {
  const searchParams = useSearchParams();
  const message = searchParams.get("oauth_error")?.trim();

  if (!message) {
    return null;
  }

  return (
    <p role="alert" className="rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
      {message}
    </p>
  );
};
