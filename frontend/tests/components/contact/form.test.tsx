// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ContactForm } from "@components/contact/form";

vi.mock("@components/ui/toast", () => ({
  useToast: () => ({ showError: vi.fn(), showSuccess: vi.fn(), showToast: vi.fn() }),
}));

vi.mock("@config/env", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@config/env")>()),
  WEB3FORMS_ACCESS_KEY: "test-key",
}));

const mockFetchSuccess = () =>
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ success: true }) }),
  );

describe("ContactForm", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("renders the form with all fields", () => {
    render(<ContactForm />);
    expect(screen.getByPlaceholderText("Example Doe")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("example@example.com")).toBeInTheDocument();
  });

  it("renders a submit button", () => {
    render(<ContactForm />);
    expect(screen.getByRole("button", { name: /send message/i })).toBeInTheDocument();
  });

  it("shows a confirmation message after submit", async () => {
    mockFetchSuccess();
    const { fireEvent } = await import("@testing-library/react");
    render(<ContactForm />);
    fireEvent.submit(screen.getByRole("button", { name: /send message/i }).closest("form")!);
    expect(await screen.findByRole("status")).toHaveTextContent(/thanks for reaching out/i);
  });

  it("hides the form after submit", async () => {
    mockFetchSuccess();
    const { fireEvent, waitFor } = await import("@testing-library/react");
    render(<ContactForm />);
    fireEvent.submit(screen.getByRole("button").closest("form")!);
    await waitFor(() => expect(screen.queryByRole("button")).not.toBeInTheDocument());
  });
});
