"use client";

import Image from "next/image";

import { Button } from "@components/ui/buttons";
import { useAuth } from "@contexts/auth";

type GoogleAuthButtonProps = {
  type?: "sign-in" | "sign-up";
  label?: string;
};

export const GoogleAuthButton = ({
  type = "sign-in",
  label = "Continue with Google",
}: GoogleAuthButtonProps) => {
  const { signInWithGoogle, signUpWithGoogle, isSubmitting } = useAuth();
  const handleClick =
    type === "sign-up" ? signUpWithGoogle : signInWithGoogle;

  return (
    <Button
      type="button"
      variant="outline"
      className="w-full"
      disabled={isSubmitting}
      onClick={handleClick}
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
  );
};
