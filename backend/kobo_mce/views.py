"""
views.py — Endpoint API untuk stack AHP-MCE.

Endpoint:
    POST /api/submit/        simpan respons pairwise satu ahli (+ validasi CR)
    GET  /api/experts/       daftar ringkas ahli yang sudah submit
    GET  /api/weights/       jalankan pipeline -> bobot global + perbandingan tipologi
    POST /api/validate/      cek konsistensi satu set pairwise tanpa menyimpan
    POST /api/narrative/     hasilkan narasi interpretasi (lapisan AI, opsional)
"""
from django.conf import settings
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import ExpertResponse, PairwiseValue
from .serializers import (SubmitResponseSerializer, ExpertResponseSummarySerializer)
from .parser import validate_response, build_matrices_for_response, BLOCK_SIZE
from .services import mce_pipeline
from .weighting import ahp
from . import ai_layer


def _save_response(data) -> ExpertResponse:
    """Simpan/replace satu ExpertResponse + PairwiseValue, lalu set is_valid."""
    with transaction.atomic():
        ExpertResponse.objects.filter(expert_id=data["expert_id"]).delete()
        resp = ExpertResponse.objects.create(
            expert_id=data["expert_id"],
            nama=data.get("nama", ""),
            instansi=data.get("instansi", ""),
            tipologi=data["tipologi"],
        )
        PairwiseValue.objects.bulk_create([
            PairwiseValue(response=resp, block=p["block"],
                          i=p["i"], j=p["j"], value=p["value"])
            for p in data["pairwise"]
        ])
        report = validate_response(resp)
        resp.is_valid = report["all_consistent"]
        resp.catatan_validasi = report["per_block"]
        resp.save(update_fields=["is_valid", "catatan_validasi"])
    return resp


@api_view(["POST"])
def submit_response(request):
    ser = SubmitResponseSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    resp = _save_response(ser.validated_data)
    return Response({
        "expert_id": resp.expert_id,
        "is_valid": resp.is_valid,
        "catatan_validasi": resp.catatan_validasi,
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def list_experts(request):
    qs = ExpertResponse.objects.all()
    data = ExpertResponseSummarySerializer(qs, many=True).data
    by_typ = {}
    for r in qs:
        by_typ[r.tipologi] = by_typ.get(r.tipologi, 0) + 1
    return Response({"total": qs.count(), "per_tipologi": by_typ, "experts": data})


@api_view(["GET"])
def compute_weights(request):
    responses = list(ExpertResponse.objects.all())
    if not responses:
        return Response({"detail": "Belum ada respons ahli."},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        result = mce_pipeline.run_pipeline(responses)
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({
        "n_experts": result["combined"]["n_experts"],
        "bobot_global": mce_pipeline.export_weights_table(result),
        "perbandingan_tipologi": mce_pipeline.typology_comparison(result),
        "konsistensi": result["combined"]["consistency_flags"],
    })


@api_view(["POST"])
def validate_only(request):
    """Cek CR satu set pairwise tanpa menyimpan (untuk feedback real-time di form)."""
    pairwise = request.data.get("pairwise", [])
    grouped = {b: {} for b in BLOCK_SIZE}
    for p in pairwise:
        grouped[p["block"]][(int(p["i"]), int(p["j"]))] = float(p["value"])
    report = {}
    for block, pairs in grouped.items():
        if not pairs and BLOCK_SIZE[block] > 2:
            continue
        M = ahp.build_matrix(BLOCK_SIZE[block], pairs)
        res = ahp.consistency_ratio(M)
        report[block] = {"CR": round(res["CR"], 4), "consistent": res["consistent"]}
    return Response({"per_block": report,
                     "all_consistent": all(r["consistent"] for r in report.values())})


@api_view(["POST"])
def narrative(request):
    """Lapisan AI: narasi interpretasi. Nonaktif jika ANTHROPIC_API_KEY kosong."""
    if not settings.ANTHROPIC_API_KEY:
        return Response({"detail": "ANTHROPIC_API_KEY tidak diset; narasi AI nonaktif."},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)
    responses = list(ExpertResponse.objects.all())
    if not responses:
        return Response({"detail": "Belum ada respons ahli."},
                        status=status.HTTP_400_BAD_REQUEST)
    result = mce_pipeline.run_pipeline(responses)
    table = mce_pipeline.export_weights_table(result)
    comp = mce_pipeline.typology_comparison(result)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        text = ai_layer.generate_narrative(table, comp, client=client)
    except Exception as e:  # noqa: BLE001
        return Response({"detail": f"Gagal memanggil API: {e}"},
                        status=status.HTTP_502_BAD_GATEWAY)
    return Response({"narrative": text})
