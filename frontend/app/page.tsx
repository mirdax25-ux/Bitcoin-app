"use client";

import { useEffect, useState } from "react";

const API = "http://127.0.0.1:8000";

type Health = {
  status: string;
  version: string;
  non_custodial: boolean;
  fund_transfers: boolean;
  private_key_storage: boolean;
};

export default function Page() {
  const [health, setHealth] = useState<Health | null>(null);
  const [address, setAddress] = useState("");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/health`).then(r => r.json()).then(setHealth).catch(() => setHealth(null));
  }, []);

  async function checkAddress() {
    setError("");
    setResult(null);
    try {
      const r = await fetch(`${API}/public/address/${encodeURIComponent(address)}`);
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Request failed");
      setResult(data);
    } catch (e: any) {
      setError(e.message || "Unknown error");
    }
  }

  return (
    <main>
      <div className="badge">NON-CUSTODIAL • WATCH-ONLY • V0.3</div>
      <h1>Bitcoin Recovery Vault</h1>
      <p className="lead">Public blockchain analysis with hard safety boundaries.</p>

      <section className="grid">
        <article><span>Backend</span><strong>{health?.status === "ok" ? "ONLINE" : "OFFLINE"}</strong></article>
        <article><span>Fund transfers</span><strong>{health?.fund_transfers ? "Enabled" : "Disabled"}</strong></article>
        <article><span>Private keys stored</span><strong>{health?.private_key_storage ? "Yes" : "0"}</strong></article>
      </section>

      <section className="panel">
        <h2>Public Bitcoin address lookup</h2>
        <div className="row">
          <input value={address} onChange={e => setAddress(e.target.value)} placeholder="Paste a public Bitcoin address" />
          <button onClick={checkAddress} disabled={!address}>Check</button>
        </div>
        {error && <p className="error">{error}</p>}
        {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
      </section>

      <section className="panel warning">
        <h2>Guardrails</h2>
        <ul>
          <li>No seed phrases or private keys.</li>
          <li>No brute force or key guessing.</li>
          <li>No fund transfers in MVP.</li>
          <li>Dormancy never proves abandonment or ownership.</li>
        </ul>
      </section>
    </main>
  );
}
