"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { getApiErrorMessage } from "@/lib/api-errors";
import { saveSession } from "@/lib/auth-session";
import { AuthService } from "@/services/auth";

export const useSignInForm = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
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

      router.push("/");
      router.refresh();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setPending(false);
    }
  };

  return {
    email,
    setEmail,
    password,
    setPassword,
    error,
    pending,
    handleSubmit,
  };
};
