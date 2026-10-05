/* Shared tax + filter persistence for the three fund desk pages. */
(function (root) {
  const KEY = "mfdesk.v1";
  const LTCG_EXEMPT = 125000;
  const STCG_RATE = 0.20;
  const LTCG_RATE = 0.125;
  const CESS = 0.04;

  function load() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "{}");
    } catch (e) {
      return {};
    }
  }
  function save(patch) {
    const s = Object.assign(load(), patch);
    localStorage.setItem(KEY, JSON.stringify(s));
  }

  function absorbHash() {
    if (!location.hash || location.hash.length < 3) return;
    try {
      const parsed = JSON.parse(decodeURIComponent(location.hash.slice(1)));
      if (parsed && typeof parsed === "object") save(Object.assign(load(), parsed));
      history.replaceState(null, "", location.pathname.split("/").pop() || location.href.split("#")[0]);
    } catch (e) {}
  }

  function syncNav() {
    document.querySelectorAll(".navlinks a").forEach((a) => {
      if (a.dataset.mfNav) return;
      a.dataset.mfNav = "1";
      a.addEventListener("click", () => {
        const href = a.getAttribute("href") || "";
        const file = href.split("#")[0];
        if (!file || file.startsWith("http")) return;
        a.setAttribute("href", file + "#" + encodeURIComponent(JSON.stringify(load())));
      });
    });
  }

  function clampDate(el, value) {
    if (!el || value == null || value === "") return;
    let v = String(value);
    if (el.min && v < el.min) v = el.min;
    if (el.max && v > el.max) v = el.max;
    el.value = v;
  }

  function setInput(el, value) {
    if (!el || value == null) return;
    if (el.type === "checkbox") {
      el.checked = !!value;
      return;
    }
    if (el.type === "date") {
      clampDate(el, value);
      return;
    }
    el.value = String(value);
  }

  function readInput(el) {
    if (!el) return null;
    if (el.type === "checkbox") return el.checked;
    return el.value;
  }

  /** Restore shared + page-prefixed fields. ids: { storageKey: elementId } */
  function restore(map) {
    absorbHash();
    syncNav();
    const s = load();
    Object.keys(map).forEach((key) => {
      const el = $(map[key]);
      if (!el) return;
      if (s[key] == null || s[key] === "") return;
      setInput(el, s[key]);
    });
    return s;
  }

  function persistFrom(map) {
    const patch = {};
    Object.keys(map).forEach((key) => {
      const el = $(map[key]);
      if (!el) return;
      patch[key] = readInput(el);
    });
    save(patch);
  }

  function bind(map, extraFn) {
    Object.keys(map).forEach((key) => {
      const el = $(map[key]);
      if (!el) return;
      const go = () => {
        persistFrom(map);
        if (extraFn) extraFn();
      };
      el.addEventListener("input", go);
      el.addEventListener("change", go);
    });
  }

  function bindScroll(page) {
    const s = load();
    const y = s[page + ".scroll"];
    if (typeof y === "number") {
      requestAnimationFrame(() => window.scrollTo(0, y));
    }
    let t = null;
    window.addEventListener("scroll", () => {
      clearTimeout(t);
      t = setTimeout(() => {
        const p = {};
        p[page + ".scroll"] = window.scrollY;
        save(p);
      }, 120);
    });
  }

  function isLongTerm(buy, sell) {
    const b = new Date(buy + "T00:00:00");
    const s = new Date(sell + "T00:00:00");
    if (Number.isNaN(b.getTime()) || Number.isNaN(s.getTime())) return false;
    const ann = new Date(b);
    ann.setFullYear(ann.getFullYear() + 1);
    return s > ann;
  }

  function lots(series, lump, sip) {
    if (!series || series.length < 2) return [];
    const endNav = series[series.length - 1][1];
    const endD = series[series.length - 1][0];
    const out = [];
    if (lump > 0) {
      out.push({
        d: series[0][0],
        amt: lump,
        units: lump / series[0][1],
        endNav,
        endD,
      });
    }
    if (sip > 0) {
      series.forEach((p) => {
        out.push({ d: p[0], amt: sip, units: sip / p[1], endNav, endD });
      });
    }
    return out;
  }

  function optsFromDom() {
    const exemptEl = $("exempt");
    const surchEl = $("surch");
    return {
      exempt: exemptEl ? Number(exemptEl.value || LTCG_EXEMPT) : LTCG_EXEMPT,
      surch: surchEl ? Number(surchEl.value || 0) : 0,
    };
  }

  function tax(lotList, opt) {
    opt = opt || optsFromDom();
    let stcg = 0;
    let ltcg = 0;
    let stAmt = 0;
    let ltAmt = 0;
    (lotList || []).forEach((lot) => {
      const gain = lot.units * lot.endNav - lot.amt;
      if (isLongTerm(lot.d, lot.endD)) {
        ltcg += gain;
        ltAmt += lot.amt;
      } else {
        stcg += gain;
        stAmt += lot.amt;
      }
    });
    let stTaxable = stcg;
    let ltTaxable = ltcg;
    if (stTaxable < 0 && ltTaxable > 0) {
      const use = Math.min(ltTaxable, -stTaxable);
      ltTaxable -= use;
      stTaxable += use;
    }
    const exempt = Math.min(Math.max(0, opt.exempt || 0), Math.max(0, ltTaxable));
    ltTaxable = Math.max(0, ltTaxable - exempt);
    stTaxable = Math.max(0, stTaxable);
    let taxAmt = stTaxable * STCG_RATE + ltTaxable * LTCG_RATE;
    taxAmt *= 1 + (opt.surch || 0);
    taxAmt *= 1 + CESS;
    const value = (lotList || []).reduce((s, lot) => s + lot.units * lot.endNav, 0);
    const invested = (lotList || []).reduce((s, lot) => s + lot.amt, 0);
    return {
      stcg,
      ltcg,
      stAmt,
      ltAmt,
      exempt,
      stTaxable,
      ltTaxable,
      tax: taxAmt,
      net: value - taxAmt,
      value,
      invested,
    };
  }

  function inr(v) {
    if (v == null || Number.isNaN(v)) return "—";
    const sign = v < 0 ? "-" : "";
    return sign + "₹" + Math.round(Math.abs(v)).toLocaleString("en-IN");
  }

  function taxBlock(t) {
    if (!t) return "";
    return `<div class="ov low" style="margin-top:12px">
      <b>If you withdraw now (Direct Growth, resident)</b>
      <div class="stats" style="margin-top:10px">
        <div class="stat"><b>${inr(t.net)}</b><span>In hand after tax</span></div>
        <div class="stat"><b>${inr(t.tax)}</b><span>Tax + 4% cess</span></div>
        <div class="stat"><b>${inr(t.stcg)}</b><span>STCG (units ≤ 12 months) · 20%</span></div>
        <div class="stat"><b>${inr(t.ltcg)}</b><span>LTCG (units &gt; 12 months) · 12.5%</span></div>
      </div>
      <div class="muted" style="margin-top:8px">
        ₹1.25 lakh LTCG exemption applied: ${inr(t.exempt)}.
        Direct vs Regular does not change this tax — Direct only lowers TER.
        Exemption is per PAN per year across all equity LTCG, not per fund.
        Surcharge not included unless you pick it. Exit load may still apply on recent SIP units.
      </div>
    </div>`;
  }

  root.MFDesk = {
    load,
    save,
    restore,
    bind,
    bindScroll,
    persistFrom,
    absorbHash,
    syncNav,
    lots,
    tax,
    optsFromDom,
    taxBlock,
    inr,
    LTCG_EXEMPT,
  };
})(window);
