// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Pagination } from "@components/ui/pagination";

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

const ITEMS = [
  { label: "1", href: "/search?page=1" },
  { label: "2", href: "/search?page=2" },
  { label: "3", href: "/search?page=3" },
];

describe("Pagination", () => {
  it("renders nothing when items is empty", () => {
    const { container } = render(<Pagination />);
    expect(container.querySelector("nav")!.childElementCount).toBe(0);
  });

  it("marks the active page with aria-current='page'", () => {
    render(<Pagination items={ITEMS} activeIndex={1} />);
    expect(screen.getByText("2").closest("[aria-current='page']")).toBeInTheDocument();
  });

  it("renders inactive pages as links when no onPageClick", () => {
    render(<Pagination items={ITEMS} activeIndex={0} />);
    expect(screen.getByRole("link", { name: "2" })).toHaveAttribute("href", "/search?page=2");
  });

  it("renders inactive pages as buttons when onPageClick is provided", () => {
    render(<Pagination items={ITEMS} activeIndex={0} onPageClick={vi.fn()} />);
    expect(screen.getByRole("button", { name: "2" })).toBeInTheDocument();
  });

  it("calls onPageClick with the correct index", async () => {
    const onPageClick = vi.fn();
    render(<Pagination items={ITEMS} activeIndex={0} onPageClick={onPageClick} />);
    await userEvent.click(screen.getByRole("button", { name: "3" }));
    expect(onPageClick).toHaveBeenCalledWith(2);
  });

  it("applies custom className to the nav", () => {
    const { container } = render(<Pagination items={ITEMS} className="mt-8" />);
    expect(container.querySelector("nav")).toHaveClass("mt-8");
  });
});
