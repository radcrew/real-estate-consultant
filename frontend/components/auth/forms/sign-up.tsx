"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { useSignUp } from "../hooks/use-sign-up";

export const SignUpForm = () => {
  const {
    email,
    setEmail,
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    error,
    pending,
    onSubmit,
  } = useSignUp();

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}
      <div className="flex flex-col gap-2">
        <label htmlFor="sign-up-email" className="text-sm font-medium">
          Email
        </label>
        <Input
          id="sign-up-email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <div className="flex flex-col gap-2">
        <label htmlFor="sign-up-password" className="text-sm font-medium">
          Password
        </label>
        <Input
          id="sign-up-password"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={72}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Use at least 8 characters (max 72).
        </p>
      </div>
      <div className="flex flex-col gap-2">
        <label htmlFor="sign-up-confirm" className="text-sm font-medium">
          Confirm password
        </label>
        <Input
          id="sign-up-confirm"
          name="confirmPassword"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={72}
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />
      </div>
      <Button type="submit" disabled={pending} className="w-full">
        {pending ? "Creating account…" : "Create account"}
      </Button>
    </form>
  );
};
