import { Logo } from "@components/ui/logo";

const AuthLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => (
  <div className="flex min-h-screen flex-col bg-neutral-100 dark:bg-neutral-950">
    <div className="flex flex-1 flex-col items-center justify-center gap-8 p-4 sm:p-6">
      <Logo className="text-xl" />
      <div className="w-full max-w-md rounded-3xl border border-neutral-200 bg-white p-8 shadow-sm dark:border-neutral-700 dark:bg-neutral-900 sm:p-10 [&_button:enabled]:cursor-pointer">
        {children}
      </div>
    </div>
  </div>
);

export default AuthLayout;
