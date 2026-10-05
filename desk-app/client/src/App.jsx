import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { api } from "./lib/utils";
import Compare from "./pages/Compare";
import Fund from "./pages/Fund";
import Funds from "./pages/Funds";
import Home from "./pages/Home";
import Learn from "./pages/Learn";

export default function App() {
  const [meta, setMeta] = useState(null);
  const [funds, setFunds] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    Promise.all([api("/api/meta"), api("/api/funds")])
      .then(([m, f]) => {
        setMeta(m);
        setFunds(f);
      })
      .catch((e) => setErr(String(e.message || e)));
  }, []);

  if (err) {
    return (
      <Layout>
        <div className="warnbox" style={{ marginTop: 40 }}>
          Cannot reach API. Start the server: <code>cd desk-app && npm run dev</code>
          <div style={{ marginTop: 8 }}>{err}</div>
        </div>
      </Layout>
    );
  }

  if (!meta || !funds.length) {
    return (
      <Layout>
        <p className="muted" style={{ marginTop: 40 }}>Loading MF Desk…</p>
      </Layout>
    );
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home meta={meta} />} />
        <Route path="/funds" element={<Funds funds={funds} />} />
        <Route path="/fund/:code" element={<Fund funds={funds} />} />
        <Route path="/compare" element={<Compare meta={meta} funds={funds} />} />
        <Route path="/inflation" element={<Navigate to="/compare#inflation" replace />} />
        <Route path="/learn" element={<Learn meta={meta} />} />
      </Routes>
    </Layout>
  );
}
