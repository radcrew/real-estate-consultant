// @vitest-environment jsdom
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PartnerLogos } from "@components/landing/partner-logos";

vi.mock("next/image", () => ({
  default: ({ alt, src, width, height }: { alt: string; src: string; width: number; height: number }) => (
    <img alt={alt} src={src} width={width} height={height} />
  ),
}));

describe("PartnerLogos", () => {
  it("renders a grid of logos", () => {
    const { container } = render(<PartnerLogos />);
    const imgs = container.querySelectorAll("img");
    expect(imgs.length).toBeGreaterThan(0);
  });

  it("renders 5 logo pairs (light+dark)", () => {
    const { container } = render(<PartnerLogos />);
    const imgs = container.querySelectorAll("img");
    expect(imgs.length).toBe(10);
  });
});
