// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BlogFeaturedCard } from "@components/blog/featured-card";
import { BlogPostCard } from "@components/blog/post-card";
import type { BlogPost } from "@components/blog/data";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

const POST: BlogPost = {
  slug: "test-post",
  title: "Test Post Title",
  excerpt: "A short excerpt about the post.",
  content: ["Paragraph one."],
  category: "Industrial",
  author: "Jane Doe",
  date: "2026-01-15",
  readingTime: "4 min read",
  image: "/images/test.jpg",
};

describe("BlogFeaturedCard", () => {
  it("renders the post title", () => {
    render(<BlogFeaturedCard post={POST} />);
    expect(screen.getByRole("heading", { name: "Test Post Title" })).toBeInTheDocument();
  });

  it("links to the correct post slug", () => {
    render(<BlogFeaturedCard post={POST} />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/blog/test-post");
  });

  it("renders the category badge", () => {
    render(<BlogFeaturedCard post={POST} />);
    expect(screen.getByText("Industrial")).toBeInTheDocument();
  });

  it("renders the excerpt", () => {
    render(<BlogFeaturedCard post={POST} />);
    expect(screen.getByText("A short excerpt about the post.")).toBeInTheDocument();
  });
});

describe("BlogPostCard", () => {
  it("renders the post title", () => {
    render(<BlogPostCard post={POST} />);
    expect(screen.getByRole("heading", { name: "Test Post Title" })).toBeInTheDocument();
  });

  it("links to the correct post slug", () => {
    render(<BlogPostCard post={POST} />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/blog/test-post");
  });

  it("renders the author name", () => {
    render(<BlogPostCard post={POST} />);
    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
  });

  it("renders the post date", () => {
    render(<BlogPostCard post={POST} />);
    expect(screen.getByText("2026-01-15")).toBeInTheDocument();
  });
});
