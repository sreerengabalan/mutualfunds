const KEY = "mfdesk.react.v1";

export const PAIR_DEFAULTS = {
  catA: "",
  catB: "",
  maxOv: "30",
  differentCats: "1",
  sort: "score",
  q: "",
  limit: "60",
};

export const FUND_DEFAULTS = {
  cat: "",
  q: "",
  sort: "aum",
};

export const COMPARE_DEFAULTS = {
  a: "",
  b: "",
  split: "65",
  histStart: "2016",
  catA: "",
  catB: "",
  lump: "300000",
  sip: "15000",
  years: "15",
};

export function loadAll() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "{}");
  } catch {
    return {};
  }
}

export function loadPage(page, defaults = {}) {
  const saved = loadAll()[page];
  if (!saved || typeof saved !== "object") return { ...defaults };
  return { ...defaults, ...saved };
}

export function savePage(page, data) {
  const all = loadAll();
  all[page] = { ...(all[page] || {}), ...data };
  localStorage.setItem(KEY, JSON.stringify(all));
}

export function toQuery(obj) {
  const qs = new URLSearchParams();
  Object.entries(obj || {}).forEach(([k, v]) => {
    if (v == null || v === "") return;
    qs.set(k, String(v));
  });
  return qs;
}

export function hrefFor(path, obj) {
  const qs = toQuery(obj).toString();
  return qs ? `${path}?${qs}` : path;
}
