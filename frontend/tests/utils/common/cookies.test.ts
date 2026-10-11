import { describe, expect, it } from "vitest";
import { getRequestCookie } from "@utils/common/cookies";

const requestWith = (cookie?: string) =>
  new Request("https://app.test/", { headers: cookie ? { cookie } : {} });

describe("getRequestCookie", () => {
  it("returns the decoded value of the named cookie", () => {
    expect(getRequestCookie(requestWith("a=1; next=%2Fsaved%3Fx%3D1; b=2"), "next")).toBe(
      "/saved?x=1",
    );
  });

  it("returns null when there is no Cookie header", () => {
    expect(getRequestCookie(requestWith(), "next")).toBeNull();
  });

  it("returns null when the cookie is missing or empty", () => {
    expect(getRequestCookie(requestWith("other=1"), "next")).toBeNull();
    expect(getRequestCookie(requestWith("next="), "next")).toBeNull();
  });

  it("does not match a cookie whose name only ends with the requested name", () => {
    expect(getRequestCookie(requestWith("not_next=%2Fevil"), "next")).toBeNull();
  });

  it("returns null for a value that is not valid URI encoding", () => {
    expect(getRequestCookie(requestWith("next=%E0%A4%A"), "next")).toBeNull();
  });
});
