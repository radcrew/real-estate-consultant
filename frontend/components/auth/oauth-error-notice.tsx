"use client";

import { useSearchParams } from "next/navigation";

export const OAuthErrorNotice = () => {
  const searchParams = useSearchParams();
  const message = searchParams.get("oauth_error")?.trim();

  if (!message) {
    return null;
  }

  return (
    <p role="alert" className="rounded-none border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
      {message}
    </p>
  );
};
