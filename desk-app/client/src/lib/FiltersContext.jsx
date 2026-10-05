import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  COMPARE_DEFAULTS,
  FUND_DEFAULTS,
  PAIR_DEFAULTS,
  hrefFor,
  loadPage,
  savePage,
} from "./persist";

const FiltersContext = createContext(null);

export function FiltersProvider({ children }) {
  const [pairs, setPairsState] = useState(() => loadPage("pairs", PAIR_DEFAULTS));
  const [funds, setFundsState] = useState(() => loadPage("funds", FUND_DEFAULTS));
  const [compare, setCompareState] = useState(() => loadPage("compare", COMPARE_DEFAULTS));

  useEffect(() => savePage("pairs", pairs), [pairs]);
  useEffect(() => savePage("funds", funds), [funds]);
  useEffect(() => savePage("compare", compare), [compare]);

  const setPairs = useCallback((patch) => {
    setPairsState((prev) => ({ ...prev, ...(typeof patch === "function" ? patch(prev) : patch) }));
  }, []);
  const setFunds = useCallback((patch) => {
    setFundsState((prev) => ({ ...prev, ...(typeof patch === "function" ? patch(prev) : patch) }));
  }, []);
  const setCompare = useCallback((patch) => {
    setCompareState((prev) => ({ ...prev, ...(typeof patch === "function" ? patch(prev) : patch) }));
  }, []);

  const value = useMemo(
    () => ({
      pairs,
      setPairs,
      funds,
      setFunds,
      compare,
      setCompare,
      pairsHref: hrefFor("/", pairs),
      fundsHref: hrefFor("/funds", funds),
      compareHref: hrefFor("/compare", compare),
    }),
    [pairs, funds, compare, setPairs, setFunds, setCompare]
  );

  return <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>;
}

export function useFilters() {
  const ctx = useContext(FiltersContext);
  if (!ctx) throw new Error("useFilters must be used inside FiltersProvider");
  return ctx;
}
