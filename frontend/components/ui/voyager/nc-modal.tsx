"use client";

import {
  Dialog,
  DialogBackdrop,
  DialogPanel,
  DialogTitle,
} from "@headlessui/react";
import { useEffect, useState, type ReactNode } from "react";

import { Button } from "@components/ui/voyager/button";
import { ButtonClose } from "@components/ui/voyager/button-close";
import { cn } from "@utils/common";

/**
 * Voyager-styled modal.
 *
 * Ported from Voyager's `shared/NcModal.tsx`. Voyager used Headless UI v1
 * (`Dialog.Overlay`, `Transition.Child`), which was removed in v2 — the React
 * 19-compatible major. Rewritten with the v2 API (`DialogBackdrop`/
 * `DialogPanel`/`DialogTitle` + the `transition` prop with `data-[closed]:`
 * utilities) and flex centering instead of the inline-block trick. Reuses the
 * ported `Button`/`ButtonClose`. Supports both controlled (`isOpenProp`) and
 * uncontrolled use.
 */
export interface NcModalProps {
  renderContent: () => ReactNode;
  renderTrigger?: (openModal: () => void) => ReactNode;
  contentExtraClass?: string;
  contentPaddingClass?: string;
  triggerText?: ReactNode;
  modalTitle?: ReactNode;
  isOpenProp?: boolean;
  onCloseModal?: () => void;
}

export const NcModal = ({
  renderTrigger,
  renderContent,
  contentExtraClass = "max-w-screen-xl",
  contentPaddingClass = "py-4 px-6 md:py-5",
  triggerText = "Open Modal",
  modalTitle = "Modal title",
  isOpenProp,
  onCloseModal,
}: NcModalProps) => {
  const [isOpen, setIsOpen] = useState(!!isOpenProp);

  const closeModal = () => {
    if (typeof isOpenProp !== "boolean") {
      setIsOpen(false);
    }
    onCloseModal?.();
  };

  const openModal = () => {
    if (typeof isOpenProp !== "boolean") {
      setIsOpen(true);
    }
  };

  useEffect(() => {
    setIsOpen(!!isOpenProp);
  }, [isOpenProp]);

  return (
    <div>
      {renderTrigger ? (
        renderTrigger(openModal)
      ) : (
        <Button onClick={openModal}>{triggerText}</Button>
      )}

      <Dialog open={isOpen} onClose={closeModal} className="relative z-50">
        <DialogBackdrop
          transition
          className="fixed inset-0 bg-neutral-900/50 duration-75 ease-out data-[closed]:opacity-0 dark:bg-black/80"
        />
        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-1 text-center md:p-4">
            <DialogPanel
              transition
              className={cn(
                "my-5 inline-block w-full transform overflow-hidden rounded-2xl border border-black/5 bg-white text-left align-middle text-neutral-900 shadow-xl transition-all sm:my-8",
                "duration-75 ease-out data-[closed]:scale-95 data-[closed]:opacity-0",
                "dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300",
                contentExtraClass,
              )}
            >
              <div className="relative border-b border-neutral-100 px-6 py-4 text-center md:py-5 dark:border-neutral-700">
                <ButtonClose
                  onClick={closeModal}
                  className="absolute left-2 top-1/2 -translate-y-1/2 sm:left-4"
                />
                {modalTitle && (
                  <DialogTitle
                    as="h3"
                    className="mx-10 text-base font-semibold text-neutral-900 lg:text-xl dark:text-neutral-200"
                  >
                    {modalTitle}
                  </DialogTitle>
                )}
              </div>
              <div className={contentPaddingClass}>{renderContent()}</div>
            </DialogPanel>
          </div>
        </div>
      </Dialog>
    </div>
  );
};

export default NcModal;
