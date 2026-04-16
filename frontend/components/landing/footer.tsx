const FOOTER =
  "border-t border-border/60 bg-muted/30 text-center text-sm text-muted-foreground";

const INNER =
  "mx-auto flex h-16 max-w-screen-xl items-center justify-center px-4";

export const Footer = () => {
  const year = new Date().getFullYear();

  return (
    <footer className={FOOTER}>
      <div className={INNER}>
        RadEstate © {year} — Built by RadCrew
      </div>
    </footer>
  );
};
