"""Generate the fund-explorer canvas from selected_50.json."""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path(__file__).parent / "output" / "equity" / "selected_50.json"
OUT = Path.home() / ".cursor" / "projects" / "c-Users-sreerengabalans-Desktop-Cursor-Projects-mf" / "canvases" / "fund-explorer.canvas.tsx"

UI = r'''import {
  BarChart,
  Button,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Checkbox,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Select,
  Stack,
  Stat,
  Table,
  Text,
  TextInput,
  useCanvasState,
} from "cursor/canvas";

type Sector = { s: string; w: number };
type Fund = {
  code: number;
  name: string;
  full: string;
  house: string;
  cat: string;
  nav: number | null;
  navd: string | null;
  yrs: number | null;
  incept: string | null;
  aum: number | null;
  ter: number | null;
  mgr: string | null;
  risk: string | null;
  sip: number | null;
  load: string | null;
  y1: number | null;
  y3: number | null;
  y5: number | null;
  y10: number | null;
  sip5: number | null;
  r3: number | null;
  r3p: number | null;
  r3mn: number | null;
  r5: number | null;
  vol: number | null;
  dd: number | null;
  ddd: string | null;
  sh: number | null;
  so: number | null;
  eq: number | null;
  dt: number | null;
  cash: number | null;
  l: number | null;
  m: number | null;
  sml: number | null;
  t5: number | null;
  t10: number | null;
  hold: number | null;
  pe: number | null;
  pb: number | null;
  turn: number | null;
  sec: Sector[];
};

const FUNDS: Fund[] = __FUNDS__;

const CAT_LABEL: Record<string, string> = {
  large_cap: "Large cap",
  mid_cap: "Mid cap",
  small_cap: "Small cap",
  multi_cap: "Multi cap",
  flexi_cap: "Flexi cap",
  large_mid_cap: "Large & mid",
};

const CAT_ORDER = [
  "all",
  "large_cap",
  "mid_cap",
  "small_cap",
  "multi_cap",
  "flexi_cap",
  "large_mid_cap",
];

const DEFAULT_VIEW = FUNDS.find((f) => f.code === 118955)?.code ?? FUNDS[0].code;

function n(v: number | null | undefined, d = 2) {
  return v == null ? "—" : v.toFixed(d);
}
function aum(v: number | null | undefined) {
  if (v == null) return "—";
  return v >= 1000 ? `₹${(v / 1000).toFixed(1)}k Cr` : `₹${v.toFixed(0)} Cr`;
}
function byCode(code: number) {
  return FUNDS.find((f) => f.code === code);
}

export default function FundExplorer() {
  const [cat, setCat] = useCanvasState("cat", "all");
  const [q, setQ] = useCanvasState("q", "");
  const [sort, setSort] = useCanvasState("sort", "r3");
  const [minYrs, setMinYrs] = useCanvasState("minYrs", "0");
  const [view, setView] = useCanvasState<number>("view", DEFAULT_VIEW);
  const [cmp, setCmp] = useCanvasState<number[]>("cmp", []);

  const minY = Number(minYrs);
  const ql = q.trim().toLowerCase();
  const filtered = FUNDS.filter((f) => {
    if (cat !== "all" && f.cat !== cat) return false;
    if (minY > 0 && (f.yrs == null || f.yrs < minY)) return false;
    if (ql && !`${f.name} ${f.house} ${f.full}`.toLowerCase().includes(ql)) return false;
    return true;
  }).sort((a, b) => {
    const key = sort as keyof Fund;
    const av = a[key];
    const bv = b[key];
    const an = typeof av === "number" ? av : -1e9;
    const bn = typeof bv === "number" ? bv : -1e9;
    if (sort === "ter" || sort === "dd") return an - bn;
    return bn - an;
  });

  const fund = byCode(view) ?? FUNDS[0];
  const compared = cmp.map(byCode).filter((x): x is Fund => !!x);

  function toggleCmp(code: number) {
    setCmp((prev) => {
      if (prev.includes(code)) return prev.filter((c) => c !== code);
      if (prev.length >= 4) return prev;
      return [...prev, code];
    });
  }

  return (
    <Stack gap={20}>
      <Stack gap={6}>
        <H1>50-fund explorer</H1>
        <Text tone="secondary">
          Direct Growth shortlist across SEBI equity categories. Click a fund
          for full details. Tick up to 4 funds to compare allocations and KPIs.
          NAV as of 11 Aug 2026.
        </Text>
      </Stack>

      <Grid columns={4} gap={16}>
        <Stat value="50" label="Funds in this shortlist" />
        <Stat value={String(filtered.length)} label="Visible after filters" tone="info" />
        <Stat value={String(compared.length)} label="In compare tray (max 4)" />
        <Stat value="6" label="Categories" />
      </Grid>

      <H2>Filters</H2>
      <Row gap={8} wrap>
        {CAT_ORDER.map((id) => (
          <span key={id}>
            <Pill active={cat === id} onClick={() => setCat(id)}>
              {id === "all" ? "All categories" : CAT_LABEL[id]}
            </Pill>
          </span>
        ))}
      </Row>
      <Grid columns={3} gap={12}>
        <Stack gap={6}>
          <Text size="small" tone="secondary">
            Search name or AMC
          </Text>
          <TextInput value={q} onChange={setQ} placeholder="e.g. Parag Parikh, HDFC, mid cap" />
        </Stack>
        <Stack gap={6}>
          <Text size="small" tone="secondary">
            Sort
          </Text>
          <Select
            value={sort}
            onChange={setSort}
            options={[
              { value: "r3", label: "3Y rolling mean (high–low)" },
              { value: "y5", label: "5Y CAGR (high–low)" },
              { value: "y10", label: "10Y CAGR (high–low)" },
              { value: "aum", label: "AUM (high–low)" },
              { value: "ter", label: "TER (low–high)" },
              { value: "dd", label: "Max drawdown (least severe)" },
              { value: "sh", label: "Sharpe 3Y (high–low)" },
            ]}
          />
        </Stack>
        <Stack gap={6}>
          <Text size="small" tone="secondary">
            Minimum history
          </Text>
          <Select
            value={minYrs}
            onChange={setMinYrs}
            options={[
              { value: "0", label: "Any" },
              { value: "3", label: "3+ years" },
              { value: "5", label: "5+ years" },
              { value: "10", label: "10+ years" },
            ]}
          />
        </Stack>
      </Grid>

      {filtered.length > 0 ? (
        <Table
          stickyHeader
          striped
          headers={[
            "Compare",
            "Fund",
            "Category",
            "AUM",
            "TER %",
            "3Y %",
            "5Y %",
            "Roll 3Y %",
            "Max DD %",
            "Eq / L / M / S %",
          ]}
          columnAlign={[
            "left",
            "left",
            "left",
            "right",
            "right",
            "right",
            "right",
            "right",
            "right",
            "right",
          ]}
          rows={filtered.map((f) => [
            <span key={`c-${f.code}`}>
              <Checkbox
                checked={cmp.includes(f.code)}
                onChange={() => toggleCmp(f.code)}
              />
            </span>,
            <span key={`b-${f.code}`}>
              <Button
                variant={view === f.code ? "primary" : "ghost"}
                onClick={() => setView(f.code)}
              >
                {f.name}
              </Button>
            </span>,
            CAT_LABEL[f.cat] ?? f.cat,
            aum(f.aum),
            n(f.ter),
            n(f.y3),
            n(f.y5),
            n(f.r3),
            n(f.dd),
            `${n(f.eq, 0)} / ${n(f.l, 0)} / ${n(f.m, 0)} / ${n(f.sml, 0)}`,
          ])}
        />
      ) : null}

      <Text size="small" tone="tertiary">
        Source: AMFI category, mfapi.in NAV history, Groww allocation. Direct
        Growth only. Rolling 3Y is the mean of all 3-year windows, not a single
        trailing return.
      </Text>

      {compared.length >= 2 ? <ComparePanel funds={compared} /> : null}

      <Divider />
      <FundDetail fund={fund} />
    </Stack>
  );
}

function ComparePanel({ funds }: { funds: Fund[] }) {
  const names = funds.map((f) => f.name.replace(" Fund", "").slice(0, 22));
  return (
    <Stack gap={12}>
      <H2>Compare ({funds.length})</H2>
      <BarChart
        categories={names}
        series={[
          { name: "3Y CAGR (%)", data: funds.map((f) => f.y3 ?? 0), tone: "info" },
          { name: "3Y rolling mean (%)", data: funds.map((f) => f.r3 ?? 0), tone: "warning" },
        ]}
        valueSuffix="%"
        height={220}
      />
      <Text size="small" tone="tertiary">
        3-year CAGR vs 3-year rolling mean for the ticked funds. 5Y and 10Y are
        in the table below when the NAV history is long enough.
      </Text>
      <BarChart
        categories={names}
        stacked
        series={[
          { name: "Large cap %", data: funds.map((f) => f.l ?? 0), tone: "info" },
          { name: "Mid cap %", data: funds.map((f) => f.m ?? 0), tone: "warning" },
          { name: "Small cap %", data: funds.map((f) => f.sml ?? 0), tone: "danger" },
        ]}
        valueSuffix="%"
        height={220}
      />
      <Text size="small" tone="tertiary">
        Market-cap mix from latest Groww portfolio stats (not a SEBI mandate
        snapshot).
      </Text>
      <Table
        striped
        headers={["Metric", ...funds.map((f) => f.name.slice(0, 28))]}
        rows={[
          ["AMC", ...funds.map((f) => f.house)],
          ["Category", ...funds.map((f) => CAT_LABEL[f.cat])],
          ["AUM", ...funds.map((f) => aum(f.aum))],
          ["TER %", ...funds.map((f) => n(f.ter))],
          ["History (y)", ...funds.map((f) => n(f.yrs, 1))],
          ["1Y CAGR %", ...funds.map((f) => n(f.y1))],
          ["3Y CAGR %", ...funds.map((f) => n(f.y3))],
          ["5Y CAGR %", ...funds.map((f) => n(f.y5))],
          ["10Y CAGR %", ...funds.map((f) => n(f.y10))],
          ["SIP 5Y CAGR %", ...funds.map((f) => n(f.sip5))],
          ["Roll 3Y mean %", ...funds.map((f) => n(f.r3))],
          ["Roll 3Y positive %", ...funds.map((f) => n(f.r3p, 0))],
          ["Vol %", ...funds.map((f) => n(f.vol))],
          ["Max DD %", ...funds.map((f) => n(f.dd))],
          ["Sharpe 3Y", ...funds.map((f) => n(f.sh))],
          ["Equity %", ...funds.map((f) => n(f.eq))],
          ["Large / Mid / Small", ...funds.map((f) => `${n(f.l, 0)}/${n(f.m, 0)}/${n(f.sml, 0)}`)],
          ["Top 10 conc. %", ...funds.map((f) => n(f.t10))],
          ["Holdings", ...funds.map((f) => (f.hold == null ? "—" : String(f.hold)))],
          ["PE / PB", ...funds.map((f) => `${n(f.pe, 1)} / ${n(f.pb, 1)}`)],
        ]}
      />
    </Stack>
  );
}

function FundDetail({ fund }: { fund: Fund }) {
  const lms = [
    { label: "Large", v: fund.l ?? 0 },
    { label: "Mid", v: fund.m ?? 0 },
    { label: "Small", v: fund.sml ?? 0 },
  ];
  const assets = [
    { label: "Equity", v: fund.eq ?? 0 },
    { label: "Debt", v: fund.dt ?? 0 },
    { label: "Cash", v: fund.cash ?? 0 },
  ];
  return (
    <Stack gap={14}>
      <H2>{fund.name}</H2>
      <Text tone="secondary">
        {fund.full} · {fund.house} · {CAT_LABEL[fund.cat]} · Direct Growth
      </Text>
      <Grid columns={4} gap={16}>
        <Stat value={aum(fund.aum)} label="AUM" />
        <Stat value={n(fund.ter)} label="TER %" />
        <Stat value={n(fund.nav, 2)} label={`NAV (${fund.navd ?? "—"})`} />
        <Stat value={n(fund.yrs, 1)} label="History (years)" />
      </Grid>
      <Grid columns={4} gap={16}>
        <Stat value={`${n(fund.y3)}%`} label="3Y CAGR" tone="info" />
        <Stat value={`${n(fund.y5)}%`} label="5Y CAGR" tone="success" />
        <Stat value={`${n(fund.r3)}%`} label="3Y rolling mean" />
        <Stat value={`${n(fund.dd)}%`} label="Max drawdown" tone="danger" />
      </Grid>

      <H3>How this fund is allocated</H3>
      <Grid columns={2} gap={16}>
        <Stack gap={8}>
          <BarChart
            categories={assets.map((x) => x.label)}
            series={[{ name: "Asset allocation (%)", data: assets.map((x) => x.v), tone: "info" }]}
            valueSuffix="%"
            height={180}
          />
          <Text size="small" tone="tertiary">
            Asset mix · Groww portfolio stats · latest available
          </Text>
        </Stack>
        <Stack gap={8}>
          <BarChart
            categories={lms.map((x) => x.label)}
            series={[{ name: "Market-cap mix (%)", data: lms.map((x) => x.v), tone: "warning" }]}
            valueSuffix="%"
            height={180}
          />
          <Text size="small" tone="tertiary">
            Large / mid / small split of the equity book
          </Text>
        </Stack>
      </Grid>

      {fund.sec.length > 0 ? (
        <Stack gap={8}>
          <H3>Top sectors</H3>
          <BarChart
            horizontal
            categories={fund.sec.map((x) => x.s)}
            series={[{ name: "Weight (%)", data: fund.sec.map((x) => x.w), tone: "info" }]}
            valueSuffix="%"
            height={200}
          />
          <Text size="small" tone="tertiary">
            Sector weights inside the equity portfolio
          </Text>
        </Stack>
      ) : null}

      <Card>
        <CardHeader trailing={fund.risk ?? undefined}>{fund.house}</CardHeader>
        <CardBody>
          <Table
            framed={false}
            headers={["Field", "Value"]}
            rows={[
              ["Fund manager", fund.mgr ?? "—"],
              ["Inception (NAV series)", fund.incept ?? "—"],
              ["Min SIP", fund.sip == null ? "—" : `₹${fund.sip}`],
              ["Exit load", fund.load ?? "—"],
              ["Sharpe 3Y", n(fund.sh)],
              ["Sortino 3Y", n(fund.so)],
              ["Volatility (ann.)", `${n(fund.vol)}%`],
              ["Worst 3Y rolling window", `${n(fund.r3mn)}%`],
              ["3Y rolling windows positive", `${n(fund.r3p, 0)}%`],
              ["SIP 5Y CAGR", `${n(fund.sip5)}%`],
              ["10Y CAGR", `${n(fund.y10)}%`],
              ["Top 5 / Top 10 concentration", `${n(fund.t5)}% / ${n(fund.t10)}%`],
              ["Holdings count", fund.hold == null ? "—" : String(fund.hold)],
              ["Portfolio PE / PB", `${n(fund.pe, 1)} / ${n(fund.pb, 1)}`],
              ["Turnover", fund.turn == null ? "—" : `${n(fund.turn, 0)}%`],
              ["Max drawdown date", fund.ddd ?? "—"],
            ]}
          />
        </CardBody>
      </Card>

      <Callout tone="neutral" title="How to use this for a 10–15 year SIP">
        Compare one large-cap or flexi-cap core with one mid/small satellite.
        Prefer lower TER in the same category, 3Y rolling that stays positive,
        and a drawdown you can keep SIPs through. This is a research table, not
        a recommendation.
      </Callout>
    </Stack>
  );
}
'''

def main() -> None:
    funds = json.loads(SRC.read_text(encoding="utf-8"))
    payload = json.dumps(funds, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(UI.replace("__FUNDS__", payload), encoding="utf-8")
    print("wrote", OUT, "bytes", OUT.stat().st_size, "funds", len(funds))


if __name__ == "__main__":
    main()
