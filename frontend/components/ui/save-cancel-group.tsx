"use client";

import { Button } from "@components/ui/button-variants";

export type SaveCancelGroupProps = {
  onSave: () => void;
  onCancel: () => void;
  saving?: boolean;
  saveLabel?: string;
  cancelLabel?: string;
  savingLabel?: string;
  cancelDisabled?: boolean;
};

export const SaveCancelGroup = ({
  onSave,
  onCancel,
  saving = false,
  saveLabel = "Save",
  cancelLabel = "Cancel",
  savingLabel = "Saving…",
  cancelDisabled = false,
}: SaveCancelGroupProps) => (
  <>
    <Button
      type="button"
      variant="ghost"
      size="default"
      onClick={onCancel}
      disabled={cancelDisabled}
    >
      {cancelLabel}
    </Button>
    <Button type="button" size="default" onClick={onSave} disabled={saving}>
      {saving ? savingLabel : saveLabel}
    </Button>
  </>
);
