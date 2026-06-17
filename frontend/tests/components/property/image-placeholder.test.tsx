// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ImagePlaceholder } from "@components/property/image-placeholder";

describe("ImagePlaceholder", () => {
  it("renders a div wrapper", () => {
    const { container } = render(<ImagePlaceholder />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("displays the label when provided", () => {
    render(<ImagePlaceholder label="Sunset Villa" />);
    expect(screen.getByText("Sunset Villa")).toBeInTheDocument();
  });

  it("does not render a label element when label is absent", () => {
    render(<ImagePlaceholder />);
    expect(screen.queryByText(/.+/)).not.toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<ImagePlaceholder className="rounded-xl" />);
    expect(container.firstChild).toHaveClass("rounded-xl");
  });
});
