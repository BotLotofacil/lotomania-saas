from dataclasses import dataclass
from typing import List, Dict, Tuple
import hashlib

@dataclass
class LotomaniaConfig:
    count: int
    window: int = 50
    nucleus_size: int = 11         # núcleo fixo
    ticket_size: int = 50          # Lotomania = 50 dezenas
    diversity_overlap_max: int = 30  # controle entre bilhetes

def _stable_seed(user_id: int, base_draw_id: str, salt: str) -> int:
    s = f"{user_id}|{base_draw_id}|{salt}".encode("utf-8")
    return int(hashlib.sha256(s).hexdigest()[:12], 16)

def _cycle_scores_stub(window_results: List[List[int]]) -> Dict[int, float]:
    """
    Stub: aqui entra sua lógica real:
    - ciclo de vida (ida/volta)
    - pares/trincas recorrentes
    - penalizar dezenas "frias fracas" (conforme seu critério)
    Retorna score por dezena 0..99
    """
    scores = {i: 0.0 for i in range(100)}
    # Placeholder simples: frequência na janela
    for draw in window_results:
        for n in draw:
            scores[n] += 1.0
    return scores

def _pick_nucleus(scores: Dict[int, float], nucleus_size: int) -> List[int]:
    return sorted(sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:nucleus_size], key=lambda x: x[0])  # (n,score)
    # ^ retorna pares; ajusta abaixo

def generate_lotomania_tickets(
    user_id: int,
    base_draw_id: str,
    last_draw_numbers: List[int],
    window_results: List[List[int]],
    cfg: LotomaniaConfig
) -> Tuple[List[List[int]], List[dict]]:
    scores = _cycle_scores_stub(window_results)

    nuc_pairs = _pick_nucleus(scores, cfg.nucleus_size)
    nucleus = [n for (n, _) in nuc_pairs]

    # "periferia" = restantes ranqueadas
    ranked = [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0])) if n not in nucleus]

    tickets: List[List[int]] = []
    audits: List[dict] = []

    for i in range(cfg.count):
        # determinismo: cada bilhete tem um salt fixo
        seed = _stable_seed(user_id, base_draw_id, salt=f"ticket-{i+1}")
        start = seed % len(ranked)

        # periferia selecionada por janela circular (determinística)
        need = cfg.ticket_size - len(nucleus)
        periphery = []
        idx = start
        while len(periphery) < need:
            n = ranked[idx % len(ranked)]
            periphery.append(n)
            idx += 1

        ticket = sorted(set(nucleus + periphery))
        # garantir 50 exatas (evita set reduzir)
        if len(ticket) != cfg.ticket_size:
            # fallback determinístico: completa a partir dos menores ausentes
            missing = [n for n in range(100) if n not in ticket]
            ticket = sorted(ticket + missing[: (cfg.ticket_size - len(ticket))])

        # overlap controlado (simples): se passar, “desloca” start e tenta de novo
        tries = 0
        while tries < 20 and any(len(set(ticket) & set(t)) > cfg.diversity_overlap_max for t in tickets):
            tries += 1
            start = (start + 17) % len(ranked)  # deslocamento fixo
            periphery = []
            idx = start
            while len(periphery) < need:
                periphery.append(ranked[idx % len(ranked)])
                idx += 1
            ticket = sorted(set(nucleus + periphery))
            if len(ticket) != cfg.ticket_size:
                missing = [n for n in range(100) if n not in ticket]
                ticket = sorted(ticket + missing[: (cfg.ticket_size - len(ticket))])

        audit = {
            "lottery": "lotomania",
            "base_draw_id": base_draw_id,
            "window": cfg.window,
            "nucleus": nucleus,
            "nucleus_rule": f"top-{cfg.nucleus_size} by cycle_score (stub freq for now)",
            "diversity_overlap_max": cfg.diversity_overlap_max,
            "ticket_index": i + 1,
            "seed": seed,
            "notes": [
                "motor determinístico: user_id + base_draw_id + ticket_index",
                "núcleo fixo + periferia móvel",
                "overlap controlado com deslocamento determinístico",
                "substitua _cycle_scores_stub pela sua lógica de ciclos/pares/trincas"
            ],
        }

        tickets.append(ticket)
        audits.append(audit)

    return tickets, audits
