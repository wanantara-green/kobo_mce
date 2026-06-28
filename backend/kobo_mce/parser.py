"""
parser.py — Rekonstruksi matriks AHP dari respons tersimpan / payload Kobo mentah.

Dua jalur:
    1. parse_kobo_submission()  -> dari dict JSON Kobo ke struktur PairwiseValue.
    2. build_matrices_for_response() -> dari ExpertResponse tersimpan ke matriks numpy.

Konvensi kolom Kobo: "{block}_{i+1}_{j+1}" (1-based di form, 0-based di DB/matriks).
Contoh: konstruk_1_2, k2_1_3, k5_3_4.
"""

from __future__ import annotations
import re
import numpy as np
from .weighting import ahp

# Pola nama kolom Kobo
_COL_RE = re.compile(r"^(konstruk|k[1-5])_(\d+)_(\d+)$")

BLOCK_SIZE = {"konstruk": 5, "k1": 3, "k2": 3, "k3": 3, "k4": 3, "k5": 4}
INDICATOR_BLOCKS = ["k1", "k2", "k3", "k4", "k5"]


def parse_kobo_submission(payload: dict) -> dict:
    """
    Ekstrak nilai pairwise dari satu submission Kobo (dict).

    Mengembalikan:
        {
          "expert_id": ..., "tipologi": ...,
          "pairs": {block: {(i,j): value}},
        }
    Kolom yang tidak cocok pola pairwise diabaikan.
    """
    pairs: dict[str, dict[tuple[int, int], float]] = {b: {} for b in BLOCK_SIZE}
    for key, val in payload.items():
        m = _COL_RE.match(key.strip())
        if not m:
            continue
        block, a, b = m.group(1), int(m.group(2)) - 1, int(m.group(3)) - 1
        if a >= b:
            continue  # hanya segitiga atas
        try:
            pairs[block][(a, b)] = float(val)
        except (TypeError, ValueError):
            continue
    return {
        "expert_id": payload.get("_uuid") or payload.get("expert_id", ""),
        "tipologi": payload.get("tipologi", ""),
        "nama": payload.get("nama", ""),
        "instansi": payload.get("instansi", ""),
        "kobo_submission_id": str(payload.get("_id", "")),
        "pairs": pairs,
    }


def build_matrix_from_pairs(block: str, pairs: dict[tuple[int, int], float]) -> np.ndarray:
    """Bangun satu matriks blok; sel kosong default 1 (sama penting)."""
    n = BLOCK_SIZE[block]
    return ahp.build_matrix(n, pairs)


def build_matrices_for_response(response) -> dict[str, np.ndarray]:
    """
    Dari objek ExpertResponse (Django) -> {block: matriks numpy}.
    Mengelompokkan PairwiseValue per blok lalu memanggil ahp.build_matrix.
    """
    grouped: dict[str, dict[tuple[int, int], float]] = {b: {} for b in BLOCK_SIZE}
    for pv in response.pairwise_values.all():
        grouped[pv.block][(pv.i, pv.j)] = pv.value
    return {b: build_matrix_from_pairs(b, grouped[b]) for b in BLOCK_SIZE}


def validate_response(response) -> dict:
    """
    Cek CR tiap blok untuk satu ahli. Mengembalikan flag + ringkasan,
    dipakai untuk menandai ExpertResponse.is_valid.
    """
    mats = build_matrices_for_response(response)
    report = {}
    all_ok = True
    for block, M in mats.items():
        res = ahp.consistency_ratio(M)
        report[block] = {"CR": round(res["CR"], 4), "consistent": res["consistent"]}
        if not res["consistent"]:
            all_ok = False
    return {"all_consistent": all_ok, "per_block": report}
