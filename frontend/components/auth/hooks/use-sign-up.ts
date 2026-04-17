"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { parseErrorPayload } from "@/lib/api-errors";

export const useSignUp = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setPending(true);
    try {
      const res = await fetch("/api/auth/sign-up", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      if (!res.ok) {
        setError(await parseErrorPayload(res));
        return;
      }
      
      router.push("/sign-in?registered=1");
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
    confirmPassword,
    setConfirmPassword,
    error,
    pending,
    onSubmit,
  };
};
