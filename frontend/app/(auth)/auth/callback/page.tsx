"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { handleOAuthCallback } from "@lib/oauth-callback";

export default function AuthCallbackPage() {
  const router = useRouter();
  const [hint, setHint] = useState("Completing sign-in…");

  const handleAuthenticated = useCallback(() => {
    router.replace("/");
    router.refresh();
  }, [router]);

  const handleAuthFailed = useCallback((message: string) => {
    router.replace(`/sign-in?oauth_error=${encodeURIComponent(message)}`);
  }, [router]);

  useEffect(() => {
    let cancelled = false;
    const isCancelled = () => cancelled;

    handleOAuthCallback(
      handleAuthenticated,
      handleAuthFailed,
      isCancelled,
      setHint,
    );

    return () => {
      cancelled = true;
    };
  }, [handleAuthenticated, handleAuthFailed]);

  return (
    <div className="flex flex-col gap-2 text-center">
      <h1 className="text-lg font-semibold text-foreground">Signing you in</h1>
      <p className="text-sm text-muted-foreground">{hint}</p>
    </div>
  );
}
