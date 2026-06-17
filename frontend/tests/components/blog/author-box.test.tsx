// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BlogAuthorBox } from "@components/blog/author-box";
import type { BlogAuthor } from "@components/blog/data";

const AUTHOR: BlogAuthor = {
  name: "Jane Doe",
  role: "Senior Editor",
  bio: "Jane covers industrial real estate markets.",
};

describe("BlogAuthorBox", () => {
  it("renders the author name", () => {
    render(<BlogAuthorBox author={AUTHOR} />);
    expect(screen.getByRole("heading", { name: "Jane Doe" })).toBeInTheDocument();
  });

  it("renders the author role", () => {
    render(<BlogAuthorBox author={AUTHOR} />);
    expect(screen.getByText("Senior Editor")).toBeInTheDocument();
  });

  it("renders the author bio", () => {
    render(<BlogAuthorBox author={AUTHOR} />);
    expect(screen.getByText("Jane covers industrial real estate markets.")).toBeInTheDocument();
  });

  it("does not render bio when absent", () => {
    render(<BlogAuthorBox author={{ ...AUTHOR, bio: undefined }} />);
    expect(screen.queryByText(/covers/i)).not.toBeInTheDocument();
  });
});
