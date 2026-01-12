"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1>Qual loteria você deseja gerar?</h1>
      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginTop: 16 }}>
        <Link href="/gerar?loteria=lotomania" style={card}>Lotomania</Link>
        <div style={{ ...card, opacity: 0.5 }}>Lotofácil (em breve)</div>
        <div style={{ ...card, opacity: 0.5 }}>Mega-Sena (em breve)</div>
      </div>
      <p style={{ marginTop: 20 }}>
        <Link href="/assinatura">Minha assinatura</Link>
      </p>
    </main>
  );
}

const card: any = {
  display: "block",
  padding: 16,
  border: "1px solid #ddd",
  borderRadius: 10,
  textDecoration: "none",
  color: "inherit"
};
