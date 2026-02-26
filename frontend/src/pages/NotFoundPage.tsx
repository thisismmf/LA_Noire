import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="page">
      <h1>Page Not Found</h1>
      <p>The requested page does not exist.</p>
      <Link to="/" className="primary-button inline-block">
        Back to Home
      </Link>
    </section>
  );
}
