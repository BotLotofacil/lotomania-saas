"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "../api/client";

export default function Gerar() {
  const sp = useSearchParams();
  const loteria = sp.get("loteria") || "lotomania";
  const [count, setCount] = useState(5);
  const [window, setWindow] = useState(50);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function onGenerate() {
    setLoading(true);
    try {
      const data = await apiFetch("/generate", {
        method: "POST",
        body: JSON.stringify({ lottery: loteria, count, window })
      });
      sessionStorage.setItem("last_result", JSON.stringify(data));
      router.push("/resultado");
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1>Gerar — {loteria}</h1>

      <div style={{ marginTop: 16, display: "grid", gap: 10, maxWidth: 420 }}>
        <label>
          Quantidade de apostas (1–50)
          <input type="number" value={count} min={1} max={50}
            onChange={(e) => setCount(parseInt(e.target.value || "1"))}
            style={inp}/>
        </label>

        <label>
          Janela (20–200)
          <input type="number" value={window} min={20} max={200}
            onChange={(e) => setWindow(parseInt(e.target.value || "50"))}
            style={inp}/>
        </label>

        <button onClick={onGenerate} disabled={loading} style={btn}>
          {loading ? "Gerando..." : "Gerar agora"}
        </button>
      </div>
    </main>
  );
}

const inp: any = { width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ddd", marginTop: 6 };
const btn: any = { padding: 12, borderRadius: 10, border: "1px solid #111", background: "#111", color: "#fff", cursor: "pointer" };
