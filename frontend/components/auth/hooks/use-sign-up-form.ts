"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { getApiErrorMessage } from "@/lib/api-errors";
import { AuthService } from "@/services/auth";

export const useSignUpForm = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setPending(true);
    try {
      await AuthService.signUp({
        email: email.trim(),
        password,
      });

      router.push("/sign-in?registered=1");
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
    confirmPassword,
    setConfirmPassword,
    error,
    pending,
    handleSubmit,
  };
};
