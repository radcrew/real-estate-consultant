import type { AxiosInstance } from "axios";
import { describe, expect, it, vi } from "vitest";
import {
  AccountService,
  buildProfileUpdateBody,
  mapProfileResponseToForm,
} from "@services/account";
import type { AccountProfileResponse } from "@services/account";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const makeHttp = (data: unknown = {}) =>
  ({
    get: vi.fn().mockResolvedValue({ data }),
    post: vi.fn().mockResolvedValue({ data }),
    patch: vi.fn().mockResolvedValue({ data }),
    delete: vi.fn().mockResolvedValue({ data }),
  }) as unknown as AxiosInstance;

const baseProfile: AccountProfileResponse = {
  id: "u-1",
  email: "jane@example.com",
  first_name: "Jane",
  last_name: "Doe",
  phone: "555-0100",
  address: "1 Main St",
  city: "Austin",
  state: "TX",
  zip_code: "78701",
  country: "US",
  avatar_url: null,
};

// ---------------------------------------------------------------------------
// mapProfileResponseToForm
// ---------------------------------------------------------------------------

describe("mapProfileResponseToForm", () => {
  it("maps all fields from response to form values", () => {
    const form = mapProfileResponseToForm(baseProfile);
    expect(form.firstName).toBe("Jane");
    expect(form.lastName).toBe("Doe");
    expect(form.email).toBe("jane@example.com");
    expect(form.phone).toBe("555-0100");
    expect(form.zipCode).toBe("78701");
  });

  it("converts null fields to empty strings", () => {
    const profile = { ...baseProfile, phone: null, first_name: null, last_name: null };
    const form = mapProfileResponseToForm(profile);
    expect(form.firstName).toBe("");
    expect(form.lastName).toBe("");
    expect(form.phone).toBe("");
  });
});

// ---------------------------------------------------------------------------
// buildProfileUpdateBody
// ---------------------------------------------------------------------------

const baseForm = mapProfileResponseToForm(baseProfile);

describe("buildProfileUpdateBody", () => {
  it("returns an empty body when nothing changed", () => {
    expect(buildProfileUpdateBody(baseForm, baseForm)).toEqual({});
  });

  it("includes only changed fields", () => {
    const draft = { ...baseForm, firstName: "Janet" };
    const body = buildProfileUpdateBody(draft, baseForm);
    expect(body).toEqual({ first_name: "Janet" });
  });

  it("trims whitespace before comparing and writing", () => {
    const draft = { ...baseForm, firstName: "  Jane  " };
    expect(buildProfileUpdateBody(draft, baseForm)).toEqual({});
  });

  it("maps zipCode → zip_code in the API body", () => {
    const draft = { ...baseForm, zipCode: "90210" };
    expect(buildProfileUpdateBody(draft, baseForm)).toEqual({ zip_code: "90210" });
  });

  it("includes multiple changed fields", () => {
    const draft = { ...baseForm, firstName: "Janet", city: "Dallas" };
    const body = buildProfileUpdateBody(draft, baseForm);
    expect(body).toEqual({ first_name: "Janet", city: "Dallas" });
  });
});

// ---------------------------------------------------------------------------
// AccountService HTTP methods
// ---------------------------------------------------------------------------

describe("AccountService", () => {
  describe("getProfile", () => {
    it("calls GET /account/profile and returns data", async () => {
      const http = makeHttp(baseProfile);
      const data = await new AccountService(http).getProfile();
      expect(http.get).toHaveBeenCalledWith("/account/profile", expect.any(Object));
      expect(data).toEqual(baseProfile);
    });
  });

  describe("updateProfile", () => {
    it("calls PATCH /account/profile with body and returns data", async () => {
      const http = makeHttp(baseProfile);
      const body = { first_name: "Janet" };
      const data = await new AccountService(http).updateProfile(body);
      expect(http.patch).toHaveBeenCalledWith("/account/profile", body, expect.any(Object));
      expect(data).toEqual(baseProfile);
    });
  });

  describe("changePassword", () => {
    it("calls POST /account/password with body", async () => {
      const http = makeHttp();
      const body = { current_password: "old", new_password: "new" };
      await new AccountService(http).changePassword(body);
      expect(http.post).toHaveBeenCalledWith("/account/password", body, expect.any(Object));
    });
  });

  describe("getSavedIds", () => {
    it("calls GET /account/saved and returns property_ids array", async () => {
      const http = makeHttp({ property_ids: ["p-1", "p-2"] });
      const ids = await new AccountService(http).getSavedIds();
      expect(http.get).toHaveBeenCalledWith("/account/saved", expect.any(Object));
      expect(ids).toEqual(["p-1", "p-2"]);
    });
  });

  describe("addSaved", () => {
    it("calls POST /account/saved with property_id", async () => {
      const http = makeHttp();
      await new AccountService(http).addSaved("prop-1");
      expect(http.post).toHaveBeenCalledWith(
        "/account/saved",
        { property_id: "prop-1" },
        expect.any(Object),
      );
    });
  });

  describe("removeSaved", () => {
    it("calls DELETE /account/saved/{id} with URL-encoded id", async () => {
      const http = makeHttp();
      await new AccountService(http).removeSaved("prop/1");
      expect(http.delete).toHaveBeenCalledWith(
        `/account/saved/${encodeURIComponent("prop/1")}`,
        expect.any(Object),
      );
    });
  });

  describe("uploadAvatar", () => {
    it("calls POST /account/avatar with FormData and null Content-Type", async () => {
      const http = makeHttp(baseProfile);
      const file = new File(["content"], "avatar.png", { type: "image/png" });
      await new AccountService(http).uploadAvatar(file);
      expect(http.post).toHaveBeenCalledWith(
        "/account/avatar",
        expect.any(FormData),
        expect.objectContaining({ headers: { "Content-Type": null } }),
      );
    });
  });
});
