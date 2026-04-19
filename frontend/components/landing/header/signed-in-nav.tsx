import Image from "next/image";

import type { StoredSession } from "@lib/auth-session";

const DEFAULT_AVATAR = "/icons/avatar-default.svg";

type SignedInNavProps = {
  session: StoredSession;
};

export const SignedInNav = ({ session }: SignedInNavProps) => {
  const label = session.user.email?.trim() || "Account";
  const custom = session.user.avatarUrl?.trim();
  const src = custom && custom.length > 0 ? custom : DEFAULT_AVATAR;

  return (
    <Image
      src={src}
      alt={label}
      title={label}
      width={32}
      height={32}
      unoptimized
      className="size-8 shrink-0 rounded-full object-cover"
      referrerPolicy="no-referrer"
    />
  );
};
