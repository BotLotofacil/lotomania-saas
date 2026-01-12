"use client";

export default function Resultado() {
  const raw = typeof window !== "undefined" ? sessionStorage.getItem("last_result") : null;
  const data = raw ? JSON.parse(raw) : null;

  return (
    <main style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1>Resultado</h1>
      {!data ? (
        <p>Nenhuma geração encontrada. Vá em “Gerar”.</p>
      ) : (
        <>
          <p><b>Sessão:</b> {data.session_id}</p>
          {data.bets.map((b: any) => (
            <div key={b.index} style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12, marginTop: 12 }}>
              <div style={{ fontWeight: 700 }}>Aposta {b.index}</div>
              <div style={{ marginTop: 8, fontFamily: "monospace" }}>{b.numbers.join(" ")}</div>
              <details style={{ marginTop: 10 }}>
                <summary>Auditoria</summary>
                <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(b.audit, null, 2)}</pre>
              </details>
            </div>
          ))}
        </>
      )}
    </main>
  );
}
