"use client";

import { useCallback, useState } from "react";

import { getApiErrorMessage } from "@lib/api-errors";
import { authService } from "@services/auth";

export type SignUpCredentials = {
  email: string;
  password: string;
};

export const useSignUp = (onSuccess: () => void) => {
  const [error, setError] = useState<string | null>(null);
  const [isSigningUp, setSigningUp] = useState(false);

  const signUp = useCallback(async ({ email, password }: SignUpCredentials) => {
    setError(null);
    setSigningUp(true);

    try {
      await authService.signUp({
        email: email.trim(),
        password,
      });

      onSuccess();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSigningUp(false);
    }
  }, [onSuccess]);

  return { signUp, error, isSigningUp };
};
