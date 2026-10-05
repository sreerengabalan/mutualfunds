const CAT = {
  large_cap: "Large cap",
  mid_cap: "Mid cap",
  small_cap: "Small cap",
  multi_cap: "Multi cap",
  flexi_cap: "Flexi cap",
  large_mid_cap: "Large & mid",
};

export const CAT_ORDER = Object.keys(CAT);

export function catLabel(c) {
  return CAT[c] || c;
}

export function inr(v) {
  if (v == null || Number.isNaN(v)) return "—";
  return "₹" + Math.round(v).toLocaleString("en-IN");
}

export function n(v, d = 1) {
  if (v == null || Number.isNaN(v)) return "—";
  return Number(v).toFixed(d);
}

export async function api(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const SECTOR_COLORS = [
  "#0f4c5c", "#2a6f7a", "#c17a3a", "#6b8f71", "#8b5e4b", "#4a6fa5", "#a35d6a", "#5c6b4a",
];

export function fundPath(code) {
  return `/fund/${code}`;
}
