type AuthFormErrorProps = {
  message: string | null | undefined;
};

export const AuthFormError = ({ message }: AuthFormErrorProps) => {
  if (!message) {
    return null;
  }

  return (
    <p role="alert" className="mb-4 text-sm text-destructive">
      {message}
    </p>
  );
};
