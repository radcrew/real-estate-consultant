// @vitest-environment jsdom
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { Subscribe } from "@components/landing/subscribe";

vi.mock("@components/ui/toast", () => ({
  useToast: () => ({ showError: vi.fn(), showSuccess: vi.fn(), showToast: vi.fn() }),
}));

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

const mockFetchSuccess = () =>
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ ok: true }) }),
  );

describe("Subscribe", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("renders the heading", () => {
    render(<Subscribe />);
    expect(screen.getByRole("heading", { name: /join our newsletter/i })).toBeInTheDocument();
  });

  it("renders an email input", () => {
    render(<Subscribe />);
    expect(screen.getByPlaceholderText("Enter your email")).toBeInTheDocument();
  });

  it("renders a subscribe button", () => {
    render(<Subscribe />);
    expect(screen.getByRole("button", { name: /subscribe/i })).toBeInTheDocument();
  });

  it("shows a thank-you message after form submission", async () => {
    mockFetchSuccess();
    const { findByRole } = render(<Subscribe />);
    fireEvent.submit(screen.getByRole("button", { name: /subscribe/i }).closest("form")!);
    expect(await findByRole("status")).toHaveTextContent("Thanks for subscribing!");
  });

  it("hides the form after submission", async () => {
    mockFetchSuccess();
    render(<Subscribe />);
    fireEvent.submit(screen.getByRole("button", { name: /subscribe/i }).closest("form")!);
    const { waitFor } = await import("@testing-library/react");
    await waitFor(() =>
      expect(screen.queryByPlaceholderText("Enter your email")).not.toBeInTheDocument(),
    );
  });

  it("applies custom className", () => {
    const { container } = render(<Subscribe className="mt-8" />);
    expect(container.firstChild).toHaveClass("mt-8");
  });
});
