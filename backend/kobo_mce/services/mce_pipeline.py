"""
mce_pipeline.py — Orkestrasi pipeline AHP untuk MCE FOLUR Luwu.

Menjembatani model Django -> agregasi -> bobot global siap-MCE.
Menjalankan agregasi untuk:
    - SEMUA ahli gabungan (bobot final)
    - per TIPOLOGI (4 kategori) untuk perbandingan/triangulasi

Output bisa diekspor ke JSON/CSV untuk overlay MCE-GIS dan untuk lapisan AI.
"""

from __future__ import annotations
import numpy as np
from ..weighting import aggregate
from .. import parser as ahp_parser

INDICATOR_BLOCKS = ["k1", "k2", "k3", "k4", "k5"]
BLOCK_TO_CONSTRUCT = {"k1": "K1", "k2": "K2", "k3": "K3", "k4": "K4", "k5": "K5"}


def _collect_matrices(responses):
    """
    Dari queryset/list ExpertResponse -> struktur matriks untuk run_full_aggregation.
    Hanya menyertakan respons yang valid (is_valid=True).
    """
    construct_mats = []
    indicator_mats = {c: [] for c in aggregate.CONSTRUCTS}

    valid = [r for r in responses if getattr(r, "is_valid", True)]
    for r in valid:
        mats = ahp_parser.build_matrices_for_response(r)
        construct_mats.append(mats["konstruk"])
        for blk in INDICATOR_BLOCKS:
            indicator_mats[BLOCK_TO_CONSTRUCT[blk]].append(mats[blk])
    return construct_mats, indicator_mats, len(valid)


def run_pipeline(responses) -> dict:
    """
    Jalankan agregasi gabungan + per tipologi.

    responses: iterable ExpertResponse (mis. ExpertResponse.objects.all()).
    """
    responses = list(responses)
    if not responses:
        raise ValueError("Tidak ada respons ahli untuk diproses.")

    # --- Gabungan semua ahli ---
    cm, im, n_all = _collect_matrices(responses)
    if n_all == 0:
        raise ValueError("Tidak ada respons valid (semua CR>0.10?).")
    combined = aggregate.run_full_aggregation(cm, im)
    combined["n_experts"] = n_all

    # --- Per tipologi ---
    by_typology = {}
    typologies = sorted({r.tipologi for r in responses})
    for typ in typologies:
        subset = [r for r in responses if r.tipologi == typ]
        cm_t, im_t, n_t = _collect_matrices(subset)
        if n_t == 0:
            by_typology[typ] = {"n_experts": 0, "skipped": "tidak ada respons valid"}
            continue
        # butuh minimal 1 matriks per blok
        if any(len(im_t[c]) == 0 for c in aggregate.CONSTRUCTS):
            by_typology[typ] = {"n_experts": n_t, "skipped": "blok indikator tidak lengkap"}
            continue
        res = aggregate.run_full_aggregation(cm_t, im_t)
        res["n_experts"] = n_t
        by_typology[typ] = res

    return {"combined": combined, "by_typology": by_typology}


def export_weights_table(pipeline_result: dict) -> list[dict]:
    """Ringkas bobot global gabungan ke tabel datar siap CSV/MCE."""
    rows = []
    for r in pipeline_result["combined"]["global_weights"]:
        rows.append({
            "konstruk": r["konstruk"],
            "konstruk_label": r["konstruk_label"],
            "indikator": r["indikator"],
            "bobot_konstruk": round(r["bobot_konstruk"], 4),
            "bobot_lokal": round(r["bobot_lokal"], 4),
            "bobot_global": round(r["bobot_global_norm"], 4),
        })
    return rows


def typology_comparison(pipeline_result: dict) -> dict:
    """
    Matriks perbandingan bobot konstruk antar tipologi -> untuk triangulasi.
    Mengembalikan {konstruk: {tipologi: bobot}}.
    """
    out = {c: {} for c in aggregate.CONSTRUCTS}
    for typ, res in pipeline_result["by_typology"].items():
        if "skipped" in res:
            continue
        for c_idx, c in enumerate(aggregate.CONSTRUCTS):
            out[c][typ] = round(float(res["construct"]["priority"][c_idx]), 4)
    # tambahkan kolom gabungan
    for c_idx, c in enumerate(aggregate.CONSTRUCTS):
        out[c]["GABUNGAN"] = round(
            float(pipeline_result["combined"]["construct"]["priority"][c_idx]), 4)
    return out
