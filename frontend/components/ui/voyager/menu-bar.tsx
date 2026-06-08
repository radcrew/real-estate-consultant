"use client";

import { Dialog, DialogBackdrop, DialogPanel } from "@headlessui/react";
import { Menu } from "lucide-react";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { NavMobile } from "@components/ui/voyager/nav-mobile";
import { cn } from "@utils/common";

/**
 * Voyager-styled mobile menu trigger + slide-in drawer.
 *
 * Ported from Voyager's `shared/MenuBar.tsx`. Headless UI v1 `Transition`/
 * `Dialog.Overlay`/`Dialog.Panel` -> v2 `Dialog`/`DialogBackdrop`/`DialogPanel`
 * with the `transition` prop and `data-[closed]:` utilities. Heroicons Bars3 ->
 * lucide `Menu`. Closes automatically on route change.
 */
export interface MenuBarProps {
  className?: string;
  iconClassName?: string;
}

export const MenuBar = ({
  className = "p-2.5 rounded-lg text-neutral-700 dark:text-neutral-300",
  iconClassName = "h-8 w-8",
}: MenuBarProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  // Close the drawer on route change (adjust state during render, no effect).
  const [prevPathname, setPrevPathname] = useState(pathname);
  if (pathname !== prevPathname) {
    setPrevPathname(pathname);
    setIsOpen(false);
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className={cn(
          "flex items-center justify-center focus:outline-none",
          className,
        )}
      >
        <Menu className={iconClassName} />
      </button>

      <Dialog
        open={isOpen}
        onClose={() => setIsOpen(false)}
        className="relative z-50"
      >
        <DialogBackdrop
          transition
          className="fixed inset-0 bg-black/60 duration-300 ease-out data-[closed]:opacity-0 dark:bg-black/70"
        />
        <div className="fixed inset-0">
          <div className="flex min-h-full justify-end">
            <DialogPanel
              transition
              className="w-full max-w-md transform overflow-hidden transition duration-200 ease-out data-[closed]:translate-x-56 data-[closed]:opacity-0"
            >
              <NavMobile onClickClose={() => setIsOpen(false)} />
            </DialogPanel>
          </div>
        </div>
      </Dialog>
    </>
  );
};

