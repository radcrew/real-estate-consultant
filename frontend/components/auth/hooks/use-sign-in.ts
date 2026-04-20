"use client";

import { useCallback, useState } from "react";

import { getApiErrorMessage } from "@lib/api-errors";
import { saveSession } from "@lib/auth-session";
import { authService } from "@services/auth";

export type SignInCredentials = {
  email: string;
  password: string;
};

export const useSignIn = (onSuccess: () => void) => {
  const [error, setError] = useState<string | null>(null);
  const [isSigningIn, setSigningIn] = useState(false);

  const signIn = useCallback(async ({ email, password }: SignInCredentials) => {
    setError(null);
    setSigningIn(true);

    try {
      const {
        access_token: accessToken,
        refresh_token: refreshToken,
        expires_in: expiresIn,
        token_type: tokenType,
        user,
      } = await authService.signIn({
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
      setSigningIn(false);
    }
  }, [onSuccess]);

  return { signIn, error, isSigningIn };
};
