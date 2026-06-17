import { describe, expect, it } from "vitest";
import {
  passwordStrengthLabel,
  scorePasswordStrength,
  validatePasswordChange,
  validateProfileForm,
} from "@utils/account/validation";

// ---------------------------------------------------------------------------
// validateProfileForm
// ---------------------------------------------------------------------------

const baseProfile = {
  firstName: "Jane",
  lastName: "Doe",
  email: "jane@example.com",
  phone: "",
  address: "",
  city: "",
  state: "",
  zipCode: "",
  country: "",
};

describe("validateProfileForm", () => {
  it("returns no errors for a valid minimal form", () => {
    expect(validateProfileForm(baseProfile)).toEqual({});
  });

  describe("firstName", () => {
    it("requires a non-empty value", () => {
      expect(validateProfileForm({ ...baseProfile, firstName: "" }).firstName).toBe(
        "First name is required.",
      );
    });

    it("trims before checking", () => {
      expect(validateProfileForm({ ...baseProfile, firstName: "  " }).firstName).toBe(
        "First name is required.",
      );
    });
  });

  describe("lastName", () => {
    it("requires a non-empty value", () => {
      expect(validateProfileForm({ ...baseProfile, lastName: "" }).lastName).toBe(
        "Last name is required.",
      );
    });
  });

  describe("email", () => {
    it("requires a non-empty value", () => {
      expect(validateProfileForm({ ...baseProfile, email: "" }).email).toBe("Email is required.");
    });

    it("rejects an address without @", () => {
      expect(validateProfileForm({ ...baseProfile, email: "notanemail" }).email).toBe(
        "Email format invalid.",
      );
    });

    it("rejects an address without a domain part", () => {
      expect(validateProfileForm({ ...baseProfile, email: "a@b" }).email).toBe(
        "Email format invalid.",
      );
    });

    it("accepts a valid email", () => {
      expect(validateProfileForm({ ...baseProfile, email: "user@domain.com" }).email).toBeUndefined();
    });
  });

  describe("phone (optional)", () => {
    it("allows an empty phone", () => {
      expect(validateProfileForm({ ...baseProfile, phone: "" }).phone).toBeUndefined();
    });

    it("rejects a phone that is too short", () => {
      expect(validateProfileForm({ ...baseProfile, phone: "123" }).phone).toBe(
        "Phone number looks too short.",
      );
    });

    it("rejects a phone with invalid characters", () => {
      expect(validateProfileForm({ ...baseProfile, phone: "123abc456" }).phone).toBe(
        "Use digits and common phone symbols only.",
      );
    });

    it("accepts a valid US-style number", () => {
      expect(validateProfileForm({ ...baseProfile, phone: "+1 (555) 000-1234" }).phone).toBeUndefined();
    });
  });

  describe("zipCode (optional)", () => {
    it("allows an empty zip", () => {
      expect(validateProfileForm({ ...baseProfile, zipCode: "" }).zipCode).toBeUndefined();
    });

    it("rejects a zip that is too short", () => {
      expect(validateProfileForm({ ...baseProfile, zipCode: "ab" }).zipCode).toBe(
        "Enter a valid postal or ZIP code.",
      );
    });

    it("accepts a 5-digit US zip", () => {
      expect(validateProfileForm({ ...baseProfile, zipCode: "90210" }).zipCode).toBeUndefined();
    });

    it("accepts a Canadian-style postal code", () => {
      expect(validateProfileForm({ ...baseProfile, zipCode: "K1A 0B1" }).zipCode).toBeUndefined();
    });
  });
});

// ---------------------------------------------------------------------------
// validatePasswordChange
// ---------------------------------------------------------------------------

describe("validatePasswordChange", () => {
  const valid = {
    currentPassword: "oldpass1",
    newPassword: "newpass1",
    confirmPassword: "newpass1",
  };

  it("returns no errors for valid values", () => {
    expect(validatePasswordChange(valid)).toEqual({});
  });

  it("requires currentPassword", () => {
    expect(validatePasswordChange({ ...valid, currentPassword: "" }).currentPassword).toBe(
      "Current password is required.",
    );
  });

  it("requires newPassword", () => {
    expect(validatePasswordChange({ ...valid, newPassword: "" }).newPassword).toBe(
      "New password is required.",
    );
  });

  it("rejects a new password shorter than 8 chars", () => {
    expect(validatePasswordChange({ ...valid, newPassword: "abc", confirmPassword: "abc" }).newPassword).toBe(
      "Use at least 8 characters.",
    );
  });

  it("requires confirmPassword", () => {
    expect(validatePasswordChange({ ...valid, confirmPassword: "" }).confirmPassword).toBe(
      "Confirm your new password.",
    );
  });

  it("rejects mismatched passwords", () => {
    expect(
      validatePasswordChange({ ...valid, confirmPassword: "different1" }).confirmPassword,
    ).toBe("Passwords do not match.");
  });

  it("rejects new password equal to current password", () => {
    const same = { currentPassword: "samepass1", newPassword: "samepass1", confirmPassword: "samepass1" };
    expect(validatePasswordChange(same).newPassword).toBe(
      "New password must be different from your current password.",
    );
  });
});

// ---------------------------------------------------------------------------
// scorePasswordStrength
// ---------------------------------------------------------------------------

describe("scorePasswordStrength", () => {
  it("returns 0 for empty string", () => {
    expect(scorePasswordStrength("")).toBe(0);
  });

  it("returns 1 for a short lowercase word (only length >=8 point missing)", () => {
    // "abc" — length<8: no length points, no mixed case, no digit, no special → 0
    expect(scorePasswordStrength("abc")).toBe(0);
  });

  it("counts length >=8", () => {
    // lowercase only, >=8 chars → score 1
    expect(scorePasswordStrength("abcdefgh")).toBe(1);
  });

  it("counts length >=12", () => {
    // lowercase only, >=12 chars → score 2 (8 + 12 bonus)
    expect(scorePasswordStrength("abcdefghijkl")).toBe(2);
  });

  it("counts mixed case", () => {
    expect(scorePasswordStrength("Abcdefgh")).toBe(2); // >=8 + mixed
  });

  it("counts digit", () => {
    expect(scorePasswordStrength("abcdefg1")).toBe(2); // >=8 + digit
  });

  it("counts special character", () => {
    expect(scorePasswordStrength("abcdefg!")).toBe(2); // >=8 + special
  });

  it("caps at 4 even when all criteria met with long password", () => {
    // length>=12 (+2), mixed (+1), digit (+1), special (+1) = 5 → capped at 4
    expect(scorePasswordStrength("Abcdefghijkl1!")).toBe(4);
  });
});

// ---------------------------------------------------------------------------
// passwordStrengthLabel
// ---------------------------------------------------------------------------

describe("passwordStrengthLabel", () => {
  it.each([
    [0, "Very weak"],
    [1, "Weak"],
    [2, "Fair"],
    [3, "Good"],
    [4, "Strong"],
  ] as const)("score %i → %s", (score, label) => {
    expect(passwordStrengthLabel(score)).toBe(label);
  });
});
