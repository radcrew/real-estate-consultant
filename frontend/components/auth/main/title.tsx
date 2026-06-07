type AuthPageTitleProps = {
  title: string;
  description: string;
};

export const AuthPageTitle = ({ title, description }: AuthPageTitleProps) => (
  <div className="text-center">
    <h1 className="text-3xl font-semibold tracking-tight text-foreground">{title}</h1>
    <p className="mt-3 text-sm text-muted-foreground">{description}</p>
  </div>
);
