"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { useSignInForm } from "../hooks/use-sign-in-form";

export const SignInForm = () => {
  const {
    email,
    setEmail,
    password,
    setPassword,
    error,
    pending,
    handleSubmit,
  } = useSignInForm();

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}
      <div className="flex flex-col gap-2">
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
        />
      </div>
      <div className="flex flex-col gap-2">
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
        />
      </div>
      <Button type="submit" disabled={pending} className="w-full">
        {pending ? "Signing in…" : "Sign in"}
      </Button>
    </form>
  );
};
