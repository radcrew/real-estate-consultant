// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Avatar } from "@components/ui/avatar";

vi.mock("next/image", () => ({
  default: ({ alt, src, fill: _fill, ...props }: { alt: string; src: string; fill?: boolean }) => (
    <img alt={alt} src={src} {...props} />
  ),
}));

describe("Avatar", () => {
  it("renders the first letter of userName as initial", () => {
    render(<Avatar userName="Jane Doe" />);
    expect(screen.getByText("J")).toBeInTheDocument();
  });

  it("falls back to 'U' initial when userName is empty", () => {
    render(<Avatar userName="" />);
    expect(screen.getByText("U")).toBeInTheDocument();
  });

  it("renders an image when imgUrl is provided", () => {
    render(<Avatar imgUrl="https://example.com/photo.jpg" userName="Jane" />);
    expect(screen.getByAltText("Jane")).toBeInTheDocument();
  });

  it("does not render an image when imgUrl is absent", () => {
    render(<Avatar userName="Jane" />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("renders a check badge when hasChecked is true", () => {
    const { container } = render(<Avatar userName="Jane" hasChecked />);
    expect(container.querySelector("svg")).toBeInTheDocument();
  });

  it("applies custom sizeClass", () => {
    const { container } = render(<Avatar userName="Jane" sizeClass="h-12 w-12" />);
    expect(container.firstChild).toHaveClass("h-12", "w-12");
  });

  it("applies custom containerClassName", () => {
    const { container } = render(<Avatar userName="Jane" containerClassName="ring-2 ring-blue-500" />);
    expect(container.firstChild).toHaveClass("ring-2", "ring-blue-500");
  });
});
