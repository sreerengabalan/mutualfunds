import { Link, NavLink, useLocation } from "react-router-dom";
import { useFilters } from "../lib/FiltersContext";

export default function Layout({ children }) {
  const { pairsHref, fundsHref, compareHref } = useFilters();
  const { pathname } = useLocation();
  const on = (path) => (pathname === path || (path !== "/" && pathname.startsWith(path + "/")) ? "on" : "");

  return (
    <>
      <header className="topnav">
        <div className="topnav-inner">
          <Link to={pairsHref} className="brand">MF Desk</Link>
          <nav className="navlinks">
            <NavLink to={pairsHref} className={on("/")}>Best pairs</NavLink>
            <NavLink to={fundsHref} className={on("/funds")}>Funds</NavLink>
            <NavLink to={compareHref} className={on("/compare")}>Compare & plan</NavLink>
            <NavLink to="/learn" className={on("/learn")}>Concepts</NavLink>
          </nav>
        </div>
      </header>
      <main className="wrap">{children}</main>
    </>
  );
}
