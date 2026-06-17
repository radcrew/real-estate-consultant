// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SaveCancelGroup } from "@components/ui/save-cancel-group";

describe("SaveCancelGroup", () => {
  it("renders Save and Cancel buttons", () => {
    render(<SaveCancelGroup onSave={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("calls onSave when Save is clicked", async () => {
    const onSave = vi.fn();
    render(<SaveCancelGroup onSave={onSave} onCancel={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(onSave).toHaveBeenCalledOnce();
  });

  it("calls onCancel when Cancel is clicked", async () => {
    const onCancel = vi.fn();
    render(<SaveCancelGroup onSave={vi.fn()} onCancel={onCancel} />);
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("shows saving label and disables Save while saving", () => {
    render(<SaveCancelGroup onSave={vi.fn()} onCancel={vi.fn()} saving />);
    expect(screen.getByRole("button", { name: "Saving…" })).toBeDisabled();
  });

  it("uses custom saveLabel and cancelLabel", () => {
    render(
      <SaveCancelGroup
        onSave={vi.fn()} onCancel={vi.fn()}
        saveLabel="Update" cancelLabel="Discard"
      />,
    );
    expect(screen.getByRole("button", { name: "Update" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Discard" })).toBeInTheDocument();
  });

  it("uses custom savingLabel while saving", () => {
    render(
      <SaveCancelGroup onSave={vi.fn()} onCancel={vi.fn()} saving savingLabel="Updating…" />,
    );
    expect(screen.getByRole("button", { name: "Updating…" })).toBeInTheDocument();
  });

  it("disables Cancel when cancelDisabled is true", () => {
    render(<SaveCancelGroup onSave={vi.fn()} onCancel={vi.fn()} cancelDisabled />);
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });
});
