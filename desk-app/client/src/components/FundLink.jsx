import { Link } from "react-router-dom";
import { fundPath } from "../lib/utils";

export default function FundLink({ code, children, className = "" }) {
  if (!code) return <span>{children}</span>;
  return (
    <Link
      className={`fund-link ${className}`}
      to={fundPath(code)}
      onClick={(e) => e.stopPropagation()}
    >
      {children}
    </Link>
  );
}
