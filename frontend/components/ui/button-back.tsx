"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { buttonVariants } from "@components/ui/button-variants";
import { cn } from "@utils/common";

type HistoryBackButtonProps = {
  children?: React.ReactNode;
  className?: string;
  rowClassName?: string;
};

export const HistoryBackButton = ({
  children = "Back",
  className,
  rowClassName,
}: HistoryBackButtonProps) => {
  const router = useRouter();

  const handleClick = useCallback(() => {
    router.back();
  }, [router]);

  return (
    <div className={cn("mb-6 flex flex-wrap items-center gap-3", rowClassName)}>
      <button
        type="button"
        onClick={handleClick}
        className={cn(
          buttonVariants({ variant: "ghost", size: "sm" }),
          "gap-1.5 pl-0 text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100",
          className,
        )}
      >
        <ArrowLeft className="size-4" aria-hidden />
        {children}
      </button>
    </div>
  );
};
