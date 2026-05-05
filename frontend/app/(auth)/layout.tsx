const AuthLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => (
  <div className="flex min-h-screen flex-col bg-muted/40">
    <div className="flex flex-1 flex-col items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-8 shadow-sm [&_button:enabled]:cursor-pointer">
        {children}
      </div>
    </div>
  </div>
);

export default AuthLayout;
