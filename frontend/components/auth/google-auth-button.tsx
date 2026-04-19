"use client";

import Image from "next/image";

import { Button } from "@components/ui/button";

import { useGoogleSignIn } from "./hooks/use-google-sign-in";

type GoogleAuthButtonProps = {
  label?: string;
  /** When the email/password form is submitting, disable Google to avoid overlapping requests. */
  formPending?: boolean;
};

export const GoogleAuthButton = ({
  label = "Continue with Google",
  formPending = false,
}: GoogleAuthButtonProps) => {
  const { signInWithGoogle, error, pending } = useGoogleSignIn();

  return (
    <div className="flex flex-col gap-2">
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      <Button
        type="button"
        variant="outline"
        className="w-full"
        disabled={pending || formPending}
        onClick={signInWithGoogle}
      >
        <Image
          src="/icons/google.svg"
          alt=""
          width={16}
          height={16}
          className="size-4 shrink-0"
          aria-hidden
          unoptimized
        />
        {label}
      </Button>
    </div>
  );
};
