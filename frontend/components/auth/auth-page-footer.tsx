import Link from "next/link";

type AuthPageFooterProps = {
  prompt: string;
  linkHref: string;
  linkLabel: string;
};

export const AuthPageFooter = ({ prompt, linkHref, linkLabel }: AuthPageFooterProps) => (
  <p className="text-center text-sm text-muted-foreground">
    {prompt}{" "}
    <Link
      href={linkHref}
      className="font-semibold text-primary underline-offset-4 hover:underline"
    >
      {linkLabel}
    </Link>
  </p>
);
