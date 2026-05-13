import type { SupabaseClient, User as AuthUser } from "@supabase/supabase-js";

const asTrimmedString = (value: unknown): string | null => {
  if (typeof value !== "string") {
    return null;
  }
  const t = value.trim();
  return t.length ? t : null;
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

const coalesceName = (
  existing: string | null | undefined,
  fromOAuth: string | null,
): string | null => {
  const current = typeof existing === "string" ? existing.trim() : "";
  if (current.length > 0) {
    return current;
  }
  return fromOAuth?.trim() || null;
};

export const syncProfileNamesAfterOAuth = async (
  supabase: SupabaseClient,
  user: AuthUser,
): Promise<void> => {
  const { firstName: fromGoogleFirst, lastName: fromGoogleLast } = extractGoogleDisplayNames(user);
  if (!fromGoogleFirst && !fromGoogleLast && !user.email) {
    return;
  }

  const userId = user.id;
  const { data: existing, error: selectError } = await supabase
    .from("profiles")
    .select("first_name,last_name")
    .eq("id", userId)
    .maybeSingle();

  if (selectError) {
    console.warn("[oauth] profile select failed:", selectError.message);
    return;
  }

  const first = coalesceName(
    existing?.first_name as string | null | undefined,
    fromGoogleFirst,
  );
  const last = coalesceName(
    existing?.last_name as string | null | undefined,
    fromGoogleLast,
  );
  const email = user.email ?? null;

  if (existing) {
    const { error } = await supabase
      .from("profiles")
      .update({ email, first_name: first, last_name: last })
      .eq("id", userId);
    if (error) {
      console.warn("[oauth] profile update failed:", error.message);
    }
    return;
  }

  const { error } = await supabase.from("profiles").insert({
    id: userId,
    email,
    first_name: first,
    last_name: last,
  });
  if (error) {
    console.warn("[oauth] profile insert failed:", error.message);
  }
};
