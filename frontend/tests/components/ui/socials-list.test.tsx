// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SocialsList, type SocialItem } from "@components/ui/socials-list";

const SOCIALS: SocialItem[] = [
  { name: "Facebook", href: "https://facebook.com", icon: <span>FB</span> },
  { name: "Twitter", href: "https://twitter.com", icon: <span>TW</span> },
];

describe("SocialsList", () => {
  it("renders a link for each social item", () => {
    render(<SocialsList socials={SOCIALS} />);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(2);
  });

  it("links to the correct hrefs", () => {
    render(<SocialsList socials={SOCIALS} />);
    expect(screen.getByTitle("Facebook")).toHaveAttribute("href", "https://facebook.com");
    expect(screen.getByTitle("Twitter")).toHaveAttribute("href", "https://twitter.com");
  });

  it("opens links in a new tab", () => {
    render(<SocialsList socials={SOCIALS} />);
    screen.getAllByRole("link").forEach((link) => {
      expect(link).toHaveAttribute("target", "_blank");
    });
  });

  it("shows names when showNames is true", () => {
    render(<SocialsList socials={SOCIALS} showNames />);
    expect(screen.getByText("Facebook")).toBeInTheDocument();
    expect(screen.getByText("Twitter")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<SocialsList socials={SOCIALS} className="gap-4" />);
    expect(container.firstChild).toHaveClass("gap-4");
  });
});
