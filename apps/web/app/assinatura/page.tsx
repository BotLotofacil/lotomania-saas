"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../api/client";

export default function Assinatura() {
  const [plans, setPlans] = useState<any>(null);

  useEffect(() => {
    apiFetch("/billing/plans").then(setPlans).catch((e) => alert(e.message));
  }, []);

  async function buy(planId: string) {
    try {
      const res = await apiFetch(`/billing/checkout?plan_id=${planId}`, { method: "POST" });
      window.location.href = res.url;
    } catch (e: any) {
      alert(e.message);
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1>Assinatura</h1>
      {!plans ? <p>Carregando...</p> : (
        <>
          <p>Stripe habilitado: <b>{String(plans.enabled)}</b></p>
          <div style={{ display: "grid", gap: 10, maxWidth: 420 }}>
            <button style={btn} onClick={() => buy("1m")}>Assinar 1 mês</button>
            <button style={btn} onClick={() => buy("3m")}>Assinar 3 meses</button>
            <button style={btn} onClick={() => buy("1y")}>Assinar 1 ano</button>
          </div>
          <p style={{ marginTop: 14, opacity: 0.75 }}>
            *Se Stripe ainda estiver desabilitado, você ativa depois via variáveis de ambiente.
          </p>
        </>
      )}
    </main>
  );
}

const btn: any = { padding: 12, borderRadius: 10, border: "1px solid #111", background: "#111", color: "#fff", cursor: "pointer" };
