"use client";

import { useCallback, useState } from "react";

import { getApiErrorMessage } from "@/lib/api-errors";
import { saveSession } from "@/lib/auth-session";
import { AuthService } from "@/services/auth";

export type SignInCredentials = {
  email: string;
  password: string;
};

export const useSignIn = (onSuccess: () => void) => {
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const signIn = useCallback(async ({ email, password }: SignInCredentials) => {
    setError(null);
    setPending(true);

    try {
      const {
        access_token: accessToken,
        refresh_token: refreshToken,
        expires_in: expiresIn,
        token_type: tokenType,
        user,
      } = await AuthService.signIn({
        email: email.trim(),
        password,
      });

      saveSession({
        accessToken,
        refreshToken,
        expiresIn,
        tokenType,
        user,
      });

      onSuccess();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setPending(false);
    }
  }, [onSuccess]);

  return { signIn, error, pending };
};
