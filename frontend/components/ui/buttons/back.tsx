"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { buttonVariants } from "@components/ui/buttons";
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
          "gap-1.5 pl-0 text-muted-foreground hover:text-foreground",
          className,
        )}
      >
        <ArrowLeft className="size-4" aria-hidden />
        {children}
      </button>
    </div>
  );
};
