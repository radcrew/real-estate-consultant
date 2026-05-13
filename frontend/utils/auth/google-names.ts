import type { User as AuthUser } from "@supabase/supabase-js";

const asTrimmedString = (value: unknown): string | null => {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length ? trimmed : null;
};

export const extractGoogleDisplayNames = (user: AuthUser): {
  firstName: string | null;
  lastName: string | null;
} => {
  const meta = user.user_metadata as Record<string, unknown> | null | undefined;
  if (!meta || typeof meta !== "object") {
    return { firstName: null, lastName: null };
  }

  const given = asTrimmedString(meta.given_name);
  const family = asTrimmedString(meta.family_name);
  if (given || family) {
    return { firstName: given, lastName: family };
  }

  const full =
    asTrimmedString(meta.full_name) ??
    asTrimmedString(meta.name) ??
    asTrimmedString(meta.display_name);
  if (!full) {
    return { firstName: null, lastName: null };
  }

  const parts = full.split(/\s+/).filter(Boolean);
  if (parts.length === 1) {
    return { firstName: parts[0] ?? null, lastName: null };
  }
  return {
    firstName: parts[0] ?? null,
    lastName: parts.slice(1).join(" ") || null,
  };
};
