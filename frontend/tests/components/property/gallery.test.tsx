// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PropertyGallery } from "@components/property/gallery";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));
vi.mock("embla-carousel-react", () => ({
  default: () => [vi.fn(), undefined],
}));

describe("PropertyGallery", () => {
  it("renders placeholder when no images", () => {
    render(<PropertyGallery images={[]} alt="Empty listing" />);
    expect(screen.getByText("Empty listing")).toBeInTheDocument();
  });

  it("renders image slides when images provided", () => {
    render(<PropertyGallery images={["/img1.jpg", "/img2.jpg"]} alt="Warehouse" />);
    expect(screen.getByAltText("Warehouse 1")).toBeInTheDocument();
    expect(screen.getByAltText("Warehouse 2")).toBeInTheDocument();
  });

  it("renders prev/next navigation buttons when multiple images", () => {
    render(<PropertyGallery images={["/img1.jpg", "/img2.jpg"]} />);
    expect(screen.getByRole("button", { name: /previous photo/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /next photo/i })).toBeInTheDocument();
  });
});
