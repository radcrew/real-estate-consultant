// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DownloadApp } from "@components/landing/download-app";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

describe("DownloadApp", () => {
  it("renders the heading", () => {
    render(<DownloadApp />);
    expect(screen.getByRole("heading", { name: /mobile apps/i })).toBeInTheDocument();
  });

  it("renders the App Store link", () => {
    render(<DownloadApp />);
    expect(screen.getByAltText(/app store/i)).toBeInTheDocument();
  });

  it("renders the Google Play link", () => {
    render(<DownloadApp />);
    expect(screen.getByAltText(/google play/i)).toBeInTheDocument();
  });
});
