export type ProfileFieldKey =
  | "firstName"
  | "lastName"
  | "email"
  | "phone"
  | "address"
  | "city"
  | "state"
  | "zipCode"
  | "country";

export type ProfileFormValues = Record<ProfileFieldKey, string>;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const trim = (v: string) => v.trim();

const validateEmail = (value: string): string | null => {
  const t = trim(value);
  if (!t) return "Email is required.";
  if (!EMAIL_RE.test(t)) return "Email format invalid.";
  return null;
};

const validateFirstName = (value: string): string | null => {
  if (!trim(value)) return "First name is required.";
  return null;
};

const validateLastName = (value: string): string | null => {
  if (!trim(value)) return "Last name is required.";
  return null;
};

const validatePhone = (value: string): string | null => {
  const t = trim(value);
  if (!t) return null;
  if (t.length < 7) return "Phone number looks too short.";
  if (!/^[\d\s\-+().]{7,}$/.test(t)) return "Use digits and common phone symbols only.";
  return null;
};

const validateZipCode = (value: string): string | null => {
  const t = trim(value);
  if (!t) return null;
  if (!/^[A-Za-z0-9][A-Za-z0-9\s-]{2,14}$/.test(t)) return "Enter a valid postal or ZIP code.";
  return null;
};

export const validateProfileForm = (values: ProfileFormValues): Partial<Record<ProfileFieldKey, string>> => {
  const errors: Partial<Record<ProfileFieldKey, string>> = {};

  const fn = validateFirstName(values.firstName);
  if (fn) errors.firstName = fn;

  const ln = validateLastName(values.lastName);
  if (ln) errors.lastName = ln;

  const em = validateEmail(values.email);
  if (em) errors.email = em;

  const ph = validatePhone(values.phone);
  if (ph) errors.phone = ph;

  const zip = validateZipCode(values.zipCode);
  if (zip) errors.zipCode = zip;

  return errors;
};

export type PasswordChangeValues = {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
};

export type PasswordFieldKey = keyof PasswordChangeValues;

export const validatePasswordChange = (
  values: PasswordChangeValues,
): Partial<Record<PasswordFieldKey | "form", string>> => {
  const errors: Partial<Record<PasswordFieldKey | "form", string>> = {};

  if (!values.currentPassword) errors.currentPassword = "Current password is required.";

  if (!values.newPassword) errors.newPassword = "New password is required.";
  else if (values.newPassword.length < 8) errors.newPassword = "Use at least 8 characters.";

  if (!values.confirmPassword) errors.confirmPassword = "Confirm your new password.";
  else if (values.newPassword !== values.confirmPassword) errors.confirmPassword = "Passwords do not match.";

  if (
    values.currentPassword &&
    values.newPassword &&
    values.currentPassword === values.newPassword
  ) {
    errors.newPassword = "New password must be different from your current password.";
  }

  return errors;
};

export type ApiKeyFormValues = {
  name: string;
  /** Raw input — empty string means "never expires". */
  expiresInDays: string;
};

export type ApiKeyFieldKey = keyof ApiKeyFormValues;

/** Bounds mirror McpApiKeyCreateRequest in backend/app/schemas/account.py. */
export const API_KEY_NAME_MAX = 120;
export const API_KEY_EXPIRY_MIN = 1;
export const API_KEY_EXPIRY_MAX = 3650;

/** Pre-filled on the create form — a non-expiring credential should be a choice, not the default. */
export const API_KEY_EXPIRY_DEFAULT_DAYS = 90;

/** Keys inside this window are flagged in the list so rotation can happen before expiry. */
export const API_KEY_EXPIRY_WARNING_DAYS = 14;

export const validateApiKeyForm = (
  values: ApiKeyFormValues,
): Partial<Record<ApiKeyFieldKey | "form", string>> => {
  const errors: Partial<Record<ApiKeyFieldKey | "form", string>> = {};

  const name = trim(values.name);
  if (!name) errors.name = "Name your key so you can recognise it later.";
  else if (name.length > API_KEY_NAME_MAX)
    errors.name = `Use at most ${API_KEY_NAME_MAX} characters.`;

  const expiry = trim(values.expiresInDays);
  if (expiry) {
    const days = Number(expiry);
    if (!Number.isInteger(days))
      errors.expiresInDays = "Enter a whole number of days, or leave blank.";
    else if (days < API_KEY_EXPIRY_MIN || days > API_KEY_EXPIRY_MAX)
      errors.expiresInDays = `Choose between ${API_KEY_EXPIRY_MIN} and ${API_KEY_EXPIRY_MAX} days.`;
  }

  return errors;
};

export const scorePasswordStrength = (password: string): 0 | 1 | 2 | 3 | 4 => {
  if (!password) return 0;
  let score = 0;
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  return Math.min(4, score) as 0 | 1 | 2 | 3 | 4;
};

export const passwordStrengthLabel = (score: 0 | 1 | 2 | 3 | 4): string => {
  switch (score) {
    case 0:
      return "Very weak";
    case 1:
      return "Weak";
    case 2:
      return "Fair";
    case 3:
      return "Good";
    default:
      return "Strong";
  }
};
