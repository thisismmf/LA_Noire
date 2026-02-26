type ErrorAlertProps = {
  message?: string;
};

export function ErrorAlert({ message }: ErrorAlertProps) {
  if (!message) {
    return null;
  }

  return (
    <div className="error-alert" role="alert">
      <strong>Request Error:</strong> {message}
    </div>
  );
}
