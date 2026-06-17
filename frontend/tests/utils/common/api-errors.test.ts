import axios from "axios";
import { describe, expect, it } from "vitest";
import { getApiErrorMessage } from "@utils/common/api-errors";

const makeAxiosError = (data: unknown, status = 400) => {
  const err = new axios.AxiosError("Request failed");
  err.response = {
    status,
    data,
    headers: {},
    config: {} as never,
    statusText: "Bad Request",
  };
  return err;
};

describe("getApiErrorMessage", () => {
  it("returns fallback for non-axios errors", () => {
    expect(getApiErrorMessage(new Error("oops"))).toBe("Something went wrong. Please try again.");
  });

  it("returns fallback for plain objects", () => {
    expect(getApiErrorMessage({ message: "something" })).toBe("Something went wrong. Please try again.");
  });

  it("returns fallback when response has no detail", () => {
    expect(getApiErrorMessage(makeAxiosError({}))).toBe("Something looks off with that request. Please review your answers and try again.");
  });

  it("returns fallback when detail is an empty string", () => {
    expect(getApiErrorMessage(makeAxiosError({ detail: "   " }))).toBe("Something looks off with that request. Please review your answers and try again.");
  });

  it("extracts a string detail", () => {
    expect(getApiErrorMessage(makeAxiosError({ detail: "Not found" }))).toBe("Not found");
  });

  it("trims whitespace from string detail", () => {
    expect(getApiErrorMessage(makeAxiosError({ detail: "  Bad input  " }))).toBe("Bad input");
  });

  it("joins FastAPI validation array items", () => {
    const detail = [{ msg: "field required" }, { msg: "invalid email" }];
    expect(getApiErrorMessage(makeAxiosError({ detail }))).toBe("field required invalid email");
  });

  it("skips array items without a msg field", () => {
    const detail = [{ msg: "field required" }, { other: "ignored" }];
    expect(getApiErrorMessage(makeAxiosError({ detail }))).toBe("field required");
  });

  it("returns fallback for an empty validation array", () => {
    expect(getApiErrorMessage(makeAxiosError({ detail: [] }))).toBe("Something looks off with that request. Please review your answers and try again.");
  });
});
