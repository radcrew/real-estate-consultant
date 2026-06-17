// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { OAuthErrorNotice } from "@components/auth/notice/oauth-error";
import { SignUpNotice } from "@components/auth/notice/sign-up";

const mockGet = vi.fn();

vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: mockGet }),
}));

describe("OAuthErrorNotice", () => {
  it("renders nothing when oauth_error param is absent", () => {
    mockGet.mockReturnValue(null);
    render(<OAuthErrorNotice />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders an alert with the error message", () => {
    mockGet.mockImplementation((key: string) =>
      key === "oauth_error" ? "Google sign-in failed." : null,
    );
    render(<OAuthErrorNotice />);
    expect(screen.getByRole("alert")).toHaveTextContent("Google sign-in failed.");
  });

  it("renders nothing when oauth_error is whitespace only", () => {
    mockGet.mockReturnValue("   ");
    render(<OAuthErrorNotice />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("SignUpNotice", () => {
  it("renders nothing when registered param is absent", () => {
    mockGet.mockReturnValue(null);
    render(<SignUpNotice />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("renders a success message when registered=1", () => {
    mockGet.mockImplementation((key: string) => (key === "registered" ? "1" : null));
    render(<SignUpNotice />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Account created. Sign in with your email and password.",
    );
  });

  it("renders nothing when registered has a different value", () => {
    mockGet.mockReturnValue("2");
    render(<SignUpNotice />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
