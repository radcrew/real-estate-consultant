"use client";

import Image from "next/image";

import { NcModal } from "@components/ui/nc-modal";

/**
 * Full-screen photo modal for the listing gallery — a scrollable column of all
 * gallery images. Controlled via `isOpen` / `onClose`; built on the ported
 * `NcModal`.
 */
type PropertyGalleryModalProps = {
  images: string[];
  alt: string;
  isOpen: boolean;
  onClose: () => void;
};

export const PropertyGalleryModal = ({
  images,
  alt,
  isOpen,
  onClose,
}: PropertyGalleryModalProps) => (
  <NcModal
    isOpenProp={isOpen}
    onCloseModal={onClose}
    modalTitle="Photos"
    contentExtraClass="max-w-5xl"
    contentPaddingClass="p-2 sm:p-4"
    renderTrigger={() => null}
    renderContent={() => (
      <div className="max-h-[80vh] space-y-3 overflow-y-auto sm:space-y-4">
        {images.map((src, i) => (
          <div
            key={i}
            className="relative aspect-[16/10] overflow-hidden rounded-xl bg-neutral-100 dark:bg-neutral-800"
          >
            <Image
              src={src}
              alt={`${alt} — photo ${i + 1}`}
              fill
              sizes="(max-width: 1024px) 100vw, 1024px"
              className="object-cover"
            />
          </div>
        ))}
      </div>
    )}
  />
);
