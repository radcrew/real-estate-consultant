"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import { ImagePlus, X } from "lucide-react";

const MAX_IMAGES = 10;
const MAX_BYTES = 5 * 1024 * 1024; // 5 MB
const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];

type ImageUploadProps = {
  files: File[];
  onChange: (files: File[]) => void;
  disabled?: boolean;
};

/**
 * Multi-image picker for the list-property form. Holds the selected `File`s in
 * the parent (uploaded on submit) and shows thumbnail previews with removal.
 */
export const ImageUpload = ({ files, onChange, disabled }: ImageUploadProps) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);

  // Object-URL previews for the current files, revoked when they change/unmount.
  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files]);
  useEffect(
    () => () => previews.forEach((u) => URL.revokeObjectURL(u)),
    [previews],
  );

  const addFiles = (incoming: FileList | null) => {
    if (!incoming || incoming.length === 0) return;
    setError(null);

    const next = [...files];
    for (const file of Array.from(incoming)) {
      if (!ACCEPTED.includes(file.type)) {
        setError("Images must be JPEG, PNG, or WebP.");
        continue;
      }
      if (file.size > MAX_BYTES) {
        setError("Each image must be 5 MB or smaller.");
        continue;
      }
      if (next.length >= MAX_IMAGES) {
        setError(`You can upload at most ${MAX_IMAGES} images.`);
        break;
      }
      // Skip obvious duplicates (same name + size).
      if (next.some((f) => f.name === file.name && f.size === file.size)) {
        continue;
      }
      next.push(file);
    }
    onChange(next);
    if (inputRef.current) inputRef.current.value = "";
  };

  const removeAt = (index: number) => {
    onChange(files.filter((_, i) => i !== index));
  };

  return (
    <div>
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
        {previews.map((src, i) => (
          <div
            key={src}
            className="group relative aspect-square overflow-hidden rounded-xl border border-neutral-200 dark:border-neutral-700"
          >
            <Image src={src} alt={files[i]?.name ?? "Listing photo"} fill className="object-cover" unoptimized />
            <button
              type="button"
              onClick={() => removeAt(i)}
              disabled={disabled}
              className="absolute right-1 top-1 rounded-full bg-black/60 p-1 text-white opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100"
              aria-label={`Remove image ${i + 1}`}
            >
              <X className="size-3.5" aria-hidden />
            </button>
          </div>
        ))}

        {files.length < MAX_IMAGES && (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={disabled}
            className="flex aspect-square flex-col items-center justify-center gap-1 rounded-xl border border-dashed border-neutral-300 text-neutral-500 transition-colors hover:border-primary-400 hover:text-primary-600 disabled:opacity-60 dark:border-neutral-600 dark:text-neutral-400"
          >
            <ImagePlus className="size-6" aria-hidden />
            <span className="text-xs font-medium">Add photo</span>
          </button>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(",")}
        multiple
        className="hidden"
        onChange={(e) => addFiles(e.target.files)}
        disabled={disabled}
      />

      <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
        Up to {MAX_IMAGES} images · JPEG, PNG, or WebP · max 5 MB each.
      </p>
      {error && <p className="mt-1 text-xs text-destructive">{error}</p>}
    </div>
  );
};
