import Link from "next/link";
import { Building2 } from "lucide-react";

const AuthLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => (
  <div className="flex min-h-screen flex-col bg-muted/40">
    <header className="border-b border-border bg-background px-4 py-4">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-lg font-bold text-primary transition-opacity hover:opacity-90"
      >
        <Building2 className="size-6 shrink-0" aria-hidden />
        RadEstate
      </Link>
    </header>
    <div className="flex flex-1 flex-col items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-8 shadow-sm [&_button:enabled]:cursor-pointer">
        {children}
      </div>
    </div>
  </div>
);

export default AuthLayout;
