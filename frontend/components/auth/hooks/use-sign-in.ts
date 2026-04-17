"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { parseErrorPayload } from "@/lib/api-errors";
import { saveSession } from "@/lib/auth-session";

type SignInJson = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  user: { id: string; email: string | null };
};

export const useSignIn = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setPending(true);

    try {
      const res = await fetch("/api/auth/sign-in", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      if (!res.ok) {
        setError(await parseErrorPayload(res));
        return;
      }

      const data = (await res.json()) as SignInJson;
      saveSession({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        expiresIn: data.expires_in,
        tokenType: data.token_type,
        user: data.user,
      });
      
      router.push("/");
      router.refresh();
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
    onSubmit,
  };
};
