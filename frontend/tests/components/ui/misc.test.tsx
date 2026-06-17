// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BackgroundSection } from "@components/ui/background-section";
import { BgGlassmorphism } from "@components/ui/bg-glassmorphism";

describe("BackgroundSection", () => {
  it("renders its children", () => {
    render(<BackgroundSection><p>Content</p></BackgroundSection>);
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<BackgroundSection className="bg-blue-100" />);
    expect(container.firstChild).toHaveClass("bg-blue-100");
  });
});

describe("BgGlassmorphism", () => {
  it("renders with aria-hidden", () => {
    const { container } = render(<BgGlassmorphism />);
    expect(container.firstChild).toHaveAttribute("aria-hidden");
  });

  it("applies custom className", () => {
    const { container } = render(<BgGlassmorphism className="absolute top-0" />);
    expect(container.firstChild).toHaveClass("absolute", "top-0");
  });
});
