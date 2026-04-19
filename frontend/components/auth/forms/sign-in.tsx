"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useCallback, useState } from "react";

import { Button } from "@components/ui/button";
import { Input } from "@components/ui/input";

import { GoogleAuthButton } from "../google-auth-button";
import { useSignIn } from "../hooks/use-sign-in";

export const SignInForm = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSuccess = useCallback(() => {
    router.push("/");
    router.refresh();
  }, [router]);

  const { signIn, error, pending } = useSignIn(handleSuccess);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await signIn({ email, password });
  };

  const fieldInputClass =
    "h-8 min-h-8 px-2.5 py-0 text-sm leading-normal shadow-none";

  return (
    <div className="flex flex-col gap-5">
      <form onSubmit={handleSubmit} className="flex flex-col">

        {error && (
          <p role="alert" className="mb-4 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="flex flex-col gap-5">

          <div className="flex flex-col gap-1.5">
            <label htmlFor="sign-in-email" className="text-sm font-medium">
              Email
            </label>
            <Input
              id="sign-in-email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={fieldInputClass}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="sign-in-password" className="text-sm font-medium">
              Password
            </label>
            <Input
              id="sign-in-password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              minLength={8}
              maxLength={72}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={fieldInputClass}
            />

          </div>
        </div>

        <Button type="submit" disabled={pending} className="mt-6 w-full">
          {pending ? "Signing in…" : "Sign in"}
        </Button>

      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-card px-2 text-muted-foreground">or</span>
        </div>
      </div>

      <GoogleAuthButton formPending={pending} />
    </div>
  );
};
