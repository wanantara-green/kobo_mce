"""
ai_layer.py — Lapisan AI untuk pipeline AHP MCE FOLUR Luwu.

Tiga fungsi, sengaja dipisah dari perhitungan bobot (yang harus deterministik
& auditable). AI TIDAK pernah mengubah bobot; hanya membantu validasi & narasi.

1. detect_inconsistency()   — statistik murni: temukan sel paling bertanggung jawab
                              atas inkonsistensi (transparan, bukan black-box).
2. suggest_repair()         — usulkan nilai pengganti agar CR turun (deterministik).
3. generate_narrative()     — panggil Claude API untuk narasi interpretasi bobot
                              (satu-satunya bagian non-deterministik; opsional).
"""

from __future__ import annotations
import json
import numpy as np
from .weighting import ahp


# ----------------------------------------------------------------------
# 1. Deteksi anomali konsistensi (statistik, transparan)
# ----------------------------------------------------------------------
def detect_inconsistency(M: np.ndarray) -> dict:
    """
    Temukan sel pairwise yang paling menyimpang dari konsistensi sempurna.

    Metode: bandingkan a_ij dengan rasio bobot w_i/w_j (yang akan bernilai
    a_ij jika matriks konsisten sempurna). Rasio error terbesar = sel paling
    bermasalah. Sepenuhnya transparan, tanpa ML.
    """
    n = M.shape[0]
    res = ahp.consistency_ratio(M)
    w = res["priority"]
    deviations = []
    for i in range(n):
        for j in range(i + 1, n):
            implied = w[i] / w[j]          # rasio yang konsisten
            actual = M[i, j]               # yang diisi ahli
            err = max(actual / implied, implied / actual)  # >=1, makin besar makin buruk
            deviations.append({
                "i": i, "j": j,
                "actual": round(float(actual), 3),
                "implied": round(float(implied), 3),
                "error_ratio": round(float(err), 3),
            })
    deviations.sort(key=lambda d: d["error_ratio"], reverse=True)
    return {
        "CR": round(res["CR"], 4),
        "consistent": res["consistent"],
        "worst_cells": deviations[:3],
        "all_deviations": deviations,
    }


# ----------------------------------------------------------------------
# 2. Saran perbaikan (deterministik)
# ----------------------------------------------------------------------
def suggest_repair(M: np.ndarray, max_cells: int = 1) -> dict:
    """
    Usulkan nilai pengganti untuk sel paling bermasalah agar CR menurun.

    Mengganti a_ij dengan nilai konsisten terdekat (round ke skala Saaty 1..9),
    lalu menghitung ulang CR untuk konfirmasi perbaikan. Deterministik.
    """
    diag = detect_inconsistency(M)
    if diag["consistent"]:
        return {"needed": False, "message": "Matriks sudah konsisten (CR<=0.10).",
                "CR_before": diag["CR"]}

    M_new = M.copy()
    changes = []
    saaty_scale = np.array([1/9,1/8,1/7,1/6,1/5,1/4,1/3,1/2,1,2,3,4,5,6,7,8,9])

    for cell in diag["worst_cells"][:max_cells]:
        i, j = cell["i"], cell["j"]
        implied = cell["implied"]
        # snap rasio implied ke nilai skala Saaty terdekat
        nearest = float(saaty_scale[np.argmin(np.abs(saaty_scale - implied))])
        M_new[i, j] = nearest
        M_new[j, i] = 1.0 / nearest
        changes.append({
            "i": i, "j": j,
            "dari": round(float(M[i, j]), 3),
            "ke": round(nearest, 3),
        })

    res_after = ahp.consistency_ratio(M_new)
    return {
        "needed": True,
        "CR_before": diag["CR"],
        "CR_after": round(res_after["CR"], 4),
        "now_consistent": res_after["consistent"],
        "changes": changes,
        "matrix_after": M_new,
    }


# ----------------------------------------------------------------------
# 3. Narasi interpretasi via Claude API (opsional, non-deterministik)
# ----------------------------------------------------------------------
def build_narrative_prompt(weights_table: list[dict],
                          typology_comparison: dict) -> str:
    """Susun prompt terstruktur untuk LLM dari hasil bobot (tanpa memanggil API)."""
    payload = {
        "konteks": "Pembobotan AHP untuk zonasi MCE program FOLUR Kabupaten Luwu, "
                   "Sulawesi Selatan. 5 konstruk, 15 indikator, panel ahli 4 tipologi.",
        "bobot_global_indikator": weights_table,
        "perbandingan_bobot_konstruk_antar_tipologi": typology_comparison,
    }
    return (
        "Anda analis spasial senior. Berdasarkan hasil pembobotan AHP berikut, "
        "tulis interpretasi naratif (3-4 paragraf, bahasa Indonesia akademis) yang "
        "mencakup: (1) indikator paling dominan dan implikasinya untuk zonasi, "
        "(2) perbedaan persepsi antar tipologi ahli, (3) catatan untuk overlay MCE-GIS. "
        "Jangan mengubah angka; hanya interpretasikan.\n\nDATA:\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def generate_narrative(weights_table: list[dict],
                      typology_comparison: dict,
                      client=None, model: str = "claude-sonnet-4-6") -> str:
    """
    Hasilkan narasi interpretasi via Claude API.

    client: instance anthropic.Anthropic (di-inject agar mudah di-test/mock).
            Jika None, kembalikan prompt-nya saja (dry-run).
    """
    prompt = build_narrative_prompt(weights_table, typology_comparison)
    if client is None:
        return prompt  # dry-run: tidak memanggil API
    msg = client.messages.create(
        model=model,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
