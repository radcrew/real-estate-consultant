"use client";

import Image from "next/image";

import { ButtonSecondary } from "@components/ui/voyager/button-secondary";
import { useAuth } from "@contexts/auth";

type GoogleAuthButtonProps = {
  label?: string;
};

export const GoogleAuthButton = ({
  label = "Continue with Google",
}: GoogleAuthButtonProps) => {
  const { signInWithGoogle, isSubmitting } = useAuth();

  return (
    <ButtonSecondary
      type="button"
      className="w-full"
      disabled={isSubmitting}
      onClick={signInWithGoogle}
    >
      <Image
        src="/icons/google.svg"
        alt=""
        width={16}
        height={16}
        className="mr-2.5 size-4 shrink-0"
        aria-hidden
        unoptimized
      />
      {label}
    </ButtonSecondary>
  );
};
