import { describe, expect, it } from "vitest";
import { extractGoogleDisplayNames } from "@utils/auth/google-names";
import type { User as AuthUser } from "@supabase/supabase-js";

const makeUser = (metadata: Record<string, unknown>): AuthUser =>
  ({ user_metadata: metadata }) as AuthUser;

describe("extractGoogleDisplayNames", () => {
  it("returns nulls for empty metadata", () => {
    expect(extractGoogleDisplayNames(makeUser({}))).toEqual({
      firstName: null,
      lastName: null,
    });
  });

  it("returns nulls for null metadata", () => {
    expect(
      extractGoogleDisplayNames({ user_metadata: null } as unknown as AuthUser),
    ).toEqual({ firstName: null, lastName: null });
  });

  it("uses given_name and family_name when present", () => {
    expect(
      extractGoogleDisplayNames(makeUser({ given_name: "Jane", family_name: "Doe" })),
    ).toEqual({ firstName: "Jane", lastName: "Doe" });
  });

  it("trims whitespace from given_name and family_name", () => {
    expect(
      extractGoogleDisplayNames(makeUser({ given_name: "  Jane  ", family_name: "  Doe  " })),
    ).toEqual({ firstName: "Jane", lastName: "Doe" });
  });

  it("uses given_name alone when family_name is absent", () => {
    expect(extractGoogleDisplayNames(makeUser({ given_name: "Jane" }))).toEqual({
      firstName: "Jane",
      lastName: null,
    });
  });

  it("splits full_name into first and last", () => {
    expect(extractGoogleDisplayNames(makeUser({ full_name: "Jane Doe" }))).toEqual({
      firstName: "Jane",
      lastName: "Doe",
    });
  });

  it("handles a three-part name, joining remaining parts as last name", () => {
    expect(extractGoogleDisplayNames(makeUser({ full_name: "Mary Jane Watson" }))).toEqual({
      firstName: "Mary",
      lastName: "Jane Watson",
    });
  });

  it("returns only firstName when full_name is a single word", () => {
    expect(extractGoogleDisplayNames(makeUser({ full_name: "Cher" }))).toEqual({
      firstName: "Cher",
      lastName: null,
    });
  });

  it("falls back from full_name to name", () => {
    expect(extractGoogleDisplayNames(makeUser({ name: "Ada Lovelace" }))).toEqual({
      firstName: "Ada",
      lastName: "Lovelace",
    });
  });

  it("falls back from name to display_name", () => {
    expect(extractGoogleDisplayNames(makeUser({ display_name: "Tim Berners-Lee" }))).toEqual({
      firstName: "Tim",
      lastName: "Berners-Lee",
    });
  });

  it("prefers given_name/family_name over full_name", () => {
    expect(
      extractGoogleDisplayNames(
        makeUser({ given_name: "Jane", family_name: "Doe", full_name: "Wrong Name" }),
      ),
    ).toEqual({ firstName: "Jane", lastName: "Doe" });
  });

  it("ignores non-string metadata values", () => {
    expect(extractGoogleDisplayNames(makeUser({ given_name: 42, family_name: true }))).toEqual({
      firstName: null,
      lastName: null,
    });
  });
});
