"use client";

import Image from "next/image";

import { Button } from "@components/ui/buttons";
import { useAuth } from "@contexts/auth";

type GoogleAuthButtonProps = {
  label?: string;
};

export const GoogleAuthButton = ({
  label = "Continue with Google",
}: GoogleAuthButtonProps) => {
  const { signInWithGoogle, isSubmitting } = useAuth();

  return (
    <Button
      type="button"
      variant="outline"
      className="w-full"
      disabled={isSubmitting}
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
  );
};
