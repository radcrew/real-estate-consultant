// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Button } from "@components/ui/button";

vi.mock("next/link", () => ({
  default: ({ href, children, className, target, rel, onClick }: {
    href: string; children: React.ReactNode; className?: string;
    target?: string; rel?: string; onClick?: () => void;
  }) => <a href={href} className={className} target={target} rel={rel} onClick={onClick}>{children}</a>,
}));

describe("Button", () => {
  describe("as a button element", () => {
    it("renders a button when no href is given", () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument();
    });

    it("calls onClick when clicked", async () => {
      const onClick = vi.fn();
      render(<Button onClick={onClick}>Click</Button>);
      await userEvent.click(screen.getByRole("button"));
      expect(onClick).toHaveBeenCalledOnce();
    });

    it("is disabled when disabled prop is true", () => {
      render(<Button disabled>Disabled</Button>);
      expect(screen.getByRole("button")).toBeDisabled();
    });

    it("is disabled when loading prop is true", () => {
      render(<Button loading>Loading</Button>);
      expect(screen.getByRole("button")).toBeDisabled();
    });

    it("shows a spinner when loading", () => {
      const { container } = render(<Button loading>Save</Button>);
      expect(container.querySelector("svg")).toBeInTheDocument();
    });

    it("does not show a spinner when not loading", () => {
      const { container } = render(<Button>Save</Button>);
      expect(container.querySelector("svg")).not.toBeInTheDocument();
    });

    it("does not fire onClick when disabled", async () => {
      const onClick = vi.fn();
      render(<Button disabled onClick={onClick}>Disabled</Button>);
      await userEvent.click(screen.getByRole("button"));
      expect(onClick).not.toHaveBeenCalled();
    });
  });

  describe("as a link element", () => {
    it("renders an anchor when href is given", () => {
      render(<Button href="/about">About</Button>);
      expect(screen.getByRole("link", { name: "About" })).toHaveAttribute("href", "/about");
    });

    it("sets target=_blank and rel when targetBlank is true", () => {
      render(<Button href="/about" targetBlank>About</Button>);
      const link = screen.getByRole("link");
      expect(link).toHaveAttribute("target", "_blank");
      expect(link).toHaveAttribute("rel", "noopener noreferrer");
    });

    it("does not set target when targetBlank is false", () => {
      render(<Button href="/about">About</Button>);
      expect(screen.getByRole("link")).not.toHaveAttribute("target");
    });
  });
});
