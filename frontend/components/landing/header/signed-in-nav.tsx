import type { StoredSession } from "@lib/auth-session";

type SignedInNavProps = {
  session: StoredSession;
};

export const SignedInNav = ({ session }: SignedInNavProps) => {
  const label = session.user.email?.trim() || "Account";

  return (
    <span className="max-w-[14rem] truncate text-sm font-semibold text-foreground" title={label}>
      {label}
    </span>
  );
};
