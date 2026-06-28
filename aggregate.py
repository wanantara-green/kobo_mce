"""
aggregate.py — Agregasi AHP grup untuk pipeline MCE FOLUR Luwu.

Strategi: Aggregation of Individual Judgments (AIJ) dengan geometric mean
per sel matriks. Standar untuk AHP grup (Forman & Peniwati, 1998); valid
pada sampel kecil karena tidak bergantung pada distribusi statistik.

Alur:
    1. Kumpulkan matriks pairwise tiap ahli (per blok: konstruk + 5 indikator).
    2. Agregasi sel-demi-sel dengan geometric mean -> matriks grup.
    3. Hitung priority vector + CR matriks grup (lewat ahp.py).
    4. Bobot global indikator = bobot konstruk x bobot indikator lokal.

Bisa diagregasi untuk semua ahli sekaligus, atau per tipologi (4 kategori),
lalu dibandingkan antar tipologi.
"""

from __future__ import annotations
import numpy as np
from . import ahp

# Definisi struktur hierarki (urutan tetap, dipakai untuk parsing & pelaporan)
CONSTRUCTS = ["K1", "K2", "K3", "K4", "K5"]
CONSTRUCT_LABELS = {
    "K1": "Kesesuaian Lahan",
    "K2": "Daya Dukung Lingkungan",
    "K3": "Risiko Iklim & Bencana",
    "K4": "Nilai Konservasi",
    "K5": "Faktor Sosial-Ekonomi",
}
INDICATORS = {
    "K1": ["Kesesuaian Kakao", "Kesesuaian Padi"],
    "K2": ["Daya Dukung Lahan", "Daya Dukung Air", "Kinerja Jasa Ekosistem"],
    "K3": ["Risiko Banjir/Longsor", "Risiko Kekeringan", "Risiko Hidrometeorologi"],
    "K4": ["Kawasan ABKT", "Area Preservasi", "Fungsi Hidrologi"],
    "K5": ["Permukiman", "Infrastruktur", "Diversifikasi Komoditas", "Aktivitas Ekonomi"],
}


def aggregate_matrices(matrices: list[np.ndarray]) -> np.ndarray:
    """
    Geometric-mean agregasi (AIJ) dari beberapa matriks pairwise berukuran sama.

    Geometric mean dipilih karena mempertahankan sifat resiprokal:
    gmean(a_ij) * gmean(a_ji) = 1, sehingga matriks grup tetap valid AHP.
    """
    if not matrices:
        raise ValueError("Daftar matriks kosong.")
    shapes = {m.shape for m in matrices}
    if len(shapes) != 1:
        raise ValueError(f"Ukuran matriks tidak seragam: {shapes}.")
    stack = np.array(matrices, dtype=float)
    # geometric mean sepanjang axis ahli = exp(mean(log))
    return np.exp(np.mean(np.log(stack), axis=0))


def aggregate_block(matrices: list[np.ndarray]) -> dict:
    """Agregasi satu blok matriks lalu hitung priority + CR matriks grup."""
    G = aggregate_matrices(matrices)
    res = ahp.consistency_ratio(G)
    res["group_matrix"] = G
    res["n_experts"] = len(matrices)
    return res


def global_weights(construct_priority: np.ndarray,
                   indicator_priorities: dict[str, np.ndarray]) -> list[dict]:
    """
    Susun bobot global 15 indikator = bobot konstruk x bobot indikator lokal.

    construct_priority: vektor bobot 5 konstruk (urut sesuai CONSTRUCTS).
    indicator_priorities: {construct_code: priority_vector_indikator}.
    Mengembalikan list dict terurut dengan bobot lokal & global.
    """
    rows = []
    for c_idx, c in enumerate(CONSTRUCTS):
        w_c = float(construct_priority[c_idx])
        local = indicator_priorities[c]
        for i_idx, name in enumerate(INDICATORS[c]):
            w_local = float(local[i_idx])
            rows.append({
                "konstruk": c,
                "konstruk_label": CONSTRUCT_LABELS[c],
                "bobot_konstruk": w_c,
                "indikator": name,
                "bobot_lokal": w_local,
                "bobot_global": w_c * w_local,
            })
    # normalisasi pengaman (harusnya sudah ~1.0)
    total = sum(r["bobot_global"] for r in rows)
    for r in rows:
        r["bobot_global_norm"] = r["bobot_global"] / total
    return rows


def run_full_aggregation(construct_matrices: list[np.ndarray],
                         indicator_matrices: dict[str, list[np.ndarray]]) -> dict:
    """
    Pipeline lengkap untuk satu kelompok ahli (semua, atau satu tipologi).

    construct_matrices: list matriks 5x5 (satu per ahli).
    indicator_matrices: {construct_code: [matriks per ahli]}.
    """
    construct_res = aggregate_block(construct_matrices)
    construct_priority = construct_res["priority"]

    indicator_results = {}
    indicator_priorities = {}
    for c in CONSTRUCTS:
        res = aggregate_block(indicator_matrices[c])
        indicator_results[c] = res
        indicator_priorities[c] = res["priority"]

    gw = global_weights(construct_priority, indicator_priorities)

    return {
        "construct": construct_res,
        "indicators": indicator_results,
        "global_weights": gw,
        "consistency_flags": {
            "construct_CR": construct_res["CR"],
            "construct_ok": construct_res["consistent"],
            **{f"{c}_CR": indicator_results[c]["CR"] for c in CONSTRUCTS},
            **{f"{c}_ok": indicator_results[c]["consistent"] for c in CONSTRUCTS},
        },
    }
