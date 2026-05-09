type AuthPageTitleProps = {
  title: string;
  description: string;
};

export const AuthPageTitle = ({ title, description }: AuthPageTitleProps) => (
  <div>
    <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
    <p className="mt-2 text-sm text-muted-foreground">{description}</p>
  </div>
);
