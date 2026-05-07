"use client";

import Image from "next/image";

import { Button } from "@components/ui/button";
import { useAuth } from "@contexts/auth";

export const GoogleAuthButton = ({ label = "Continue with Google" }: { label?: string }) => {
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
