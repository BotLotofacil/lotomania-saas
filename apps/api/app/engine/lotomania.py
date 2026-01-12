from dataclasses import dataclass
from typing import List, Dict, Tuple
import hashlib
import math
from collections import Counter
import itertools

@dataclass
class LotomaniaConfig:
    count: int
    window: int = 60               # você está trabalhando com 60
    nucleus_size: int = 11         # núcleo fixo
    ticket_size: int = 50          # Lotomania = 50 dezenas
    diversity_overlap_max: int = 30  # overlap máximo entre bilhetes

    # pesos do score (ajuste fino depois)
    w_freq: float = 0.55
    w_recency: float = 0.20
    w_cycle: float = 0.25

    # alvo de ciclo: quer puxar dezenas que "estão pra voltar"
    target_gap_draws: float = 10.0
    sigma_gap_draws: float = 6.0

    # coocorrência
    w_pair: float = 0.14
    w_triple: float = 0.06
    top_pairs: int = 80
    top_triples: int = 40

def _stable_seed(user_id: int, base_draw_id: str, salt: str) -> int:
    s = f"{user_id}|{base_draw_id}|{salt}".encode("utf-8")
    return int(hashlib.sha256(s).hexdigest()[:12], 16)

def _compute_freq(window_results: List[List[int]]) -> Dict[int, float]:
    c = Counter()
    for draw in window_results:
        c.update(draw)
    maxv = max(c.values()) if c else 1
    return {n: c.get(n, 0) / maxv for n in range(100)}

def _compute_gap(window_results: List[List[int]]) -> Dict[int, int]:
    # idx 0 = mais recente, idx cresce pra trás
    last_seen = {n: None for n in range(100)}
    for idx, draw in enumerate(window_results):
        for n in draw:
            if last_seen[n] is None:
                last_seen[n] = idx
    # garantia: se algo não apareceu na janela, joga gap grande
    return {n: (last_seen[n] if last_seen[n] is not None else len(window_results) + 5) for n in range(100)}

def _cycle_bonus(gap: int, target: float, sigma: float) -> float:
    # gaussiana: pico em target_gap, cai pros lados
    z = (gap - target) / (sigma if sigma > 0 else 1.0)
    return math.exp(-0.5 * (z ** 2))

def _cooccurrence_maps(window_results: List[List[int]]):
    pair = Counter()
    triple = Counter()
    for draw in window_results:
        s = sorted(draw)
        for a, b in itertools.combinations(s, 2):
            pair[(a, b)] += 1
        for a, b, c in itertools.combinations(s, 3):
            triple[(a, b, c)] += 1
    return pair, triple

def _build_scores(window_results: List[List[int]], cfg: LotomaniaConfig) -> Tuple[Dict[int, float], dict]:
    freq = _compute_freq(window_results)
    gap = _compute_gap(window_results)

    # recência: 1/(gap+1) normalizado
    rec_raw = {n: 1.0 / (gap[n] + 1) for n in range(100)}
    rec_max = max(rec_raw.values()) if rec_raw else 1.0
    rec = {n: rec_raw[n] / rec_max for n in range(100)}

    cycle = {n: _cycle_bonus(gap[n], cfg.target_gap_draws, cfg.sigma_gap_draws) for n in range(100)}
    cycle_max = max(cycle.values()) if cycle else 1.0
    cycle = {n: cycle[n] / cycle_max for n in range(100)}

    base = {n: (cfg.w_freq * freq[n] + cfg.w_recency * rec[n] + cfg.w_cycle * cycle[n]) for n in range(100)}

    # coocorrência: pega top pares/trincas da janela e distribui bônus
    pair, triple = _cooccurrence_maps(window_results)
    topP = pair.most_common(cfg.top_pairs)
    topT = triple.most_common(cfg.top_triples)

    pair_bonus = {n: 0.0 for n in range(100)}
    for (a, b), v in topP:
        pair_bonus[a] += v
        pair_bonus[b] += v
    pb_max = max(pair_bonus.values()) if pair_bonus else 1.0
    pair_bonus = {n: (pair_bonus[n] / pb_max) if pb_max else 0.0 for n in range(100)}

    triple_bonus = {n: 0.0 for n in range(100)}
    for (a, b, c), v in topT:
        triple_bonus[a] += v
        triple_bonus[b] += v
        triple_bonus[c] += v
    tb_max = max(triple_bonus.values()) if triple_bonus else 1.0
    triple_bonus = {n: (triple_bonus[n] / tb_max) if tb_max else 0.0 for n in range(100)}

    scores = {
        n: base[n] + cfg.w_pair * pair_bonus[n] + cfg.w_triple * triple_bonus[n]
        for n in range(100)
    }

    audit_meta = {
        "weights": {
            "freq": cfg.w_freq,
            "recency": cfg.w_recency,
            "cycle": cfg.w_cycle,
            "pair": cfg.w_pair,
            "triple": cfg.w_triple,
        },
        "cycle_target_gap": cfg.target_gap_draws,
        "cycle_sigma": cfg.sigma_gap_draws,
        "top_pairs_used": cfg.top_pairs,
        "top_triples_used": cfg.top_triples,
    }

    return scores, audit_meta

def generate_lotomania_tickets(
    user_id: int,
    base_draw_id: str,
    window_results: List[List[int]],
    cfg: LotomaniaConfig
) -> Tuple[List[List[int]], List[dict]]:
    scores, meta = _build_scores(window_results, cfg)

    # 1) Núcleo fixo (top scores)
    nucleus = [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))[: cfg.nucleus_size]]

    # 2) Ranking periférico (restante por score)
    ranked = [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0])) if n not in nucleus]

    tickets: List[List[int]] = []
    audits: List[dict] = []

    for i in range(cfg.count):
        seed = _stable_seed(user_id, base_draw_id, salt=f"ticket-{i+1}")
        start = seed % len(ranked)

        need = cfg.ticket_size - len(nucleus)

        def build_ticket(start_idx: int) -> List[int]:
            periphery = []
            idx = start_idx
            while len(periphery) < need:
                periphery.append(ranked[idx % len(ranked)])
                idx += 1
            ticket = sorted(set(nucleus + periphery))
            # garante 50 exatas (fallback determinístico)
            if len(ticket) != cfg.ticket_size:
                missing = [n for n in range(100) if n not in ticket]
                ticket = sorted(ticket + missing[: (cfg.ticket_size - len(ticket))])
            return ticket

        ticket = build_ticket(start)

        # 3) Overlap controlado determinístico
        tries = 0
        while tries < 25 and any(len(set(ticket) & set(t)) > cfg.diversity_overlap_max for t in tickets):
            tries += 1
            start = (start + 17) % len(ranked)
            ticket = build_ticket(start)

        audit = {
            "lottery": "lotomania",
            "base_draw_id": base_draw_id,
            "window": cfg.window,
            "nucleus": nucleus,
            "diversity_overlap_max": cfg.diversity_overlap_max,
            "ticket_index": i + 1,
            "seed": seed,
            "meta": meta,
            "notes": [
                "determinístico: user_id + base_draw_id + ticket_index",
                "score = freq + recência + ciclo (gap alvo) + bônus de pares/trincas",
                "núcleo fixo = top scores; periferia móvel = ranking com offset determinístico",
                "overlap controlado com deslocamento determinístico"
            ],
        }

        tickets.append(ticket)
        audits.append(audit)

    return tickets, audits
