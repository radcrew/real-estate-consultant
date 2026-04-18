"use client";

import { useCallback, useState } from "react";

import { getApiErrorMessage } from "@/lib/api-errors";
import { AuthService } from "@/services/auth";

export type SignUpCredentials = {
  email: string;
  password: string;
};

export const useSignUp = (onSuccess: () => void) => {
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const signUp = useCallback(async ({ email, password }: SignUpCredentials) => {
    setError(null);
    setPending(true);

    try {
      await AuthService.signUp({
        email: email.trim(),
        password,
      });

      onSuccess();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setPending(false);
    }
  }, [onSuccess]);

  return { signUp, error, pending };
};
