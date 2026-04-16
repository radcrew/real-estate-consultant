import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <main className="mx-auto flex w-full max-w-3xl flex-col items-center gap-6 rounded-2xl border bg-card p-10 text-center shadow-sm">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-muted-foreground">
          Welcome to
        </p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">RadEstate</h1>
        <p className="max-w-2xl text-base text-muted-foreground sm:text-lg">
          A modern real estate consultant platform built with Next.js, Tailwind
          CSS, and shadcn/ui.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button size="lg">Get Started</Button>
          <Button variant="outline" size="lg">
            Explore Properties
          </Button>
        </div>
      </main>
    </div>
  );
}
