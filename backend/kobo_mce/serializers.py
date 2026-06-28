"""
serializers.py — Serializer DRF untuk submit pairwise & baca hasil.
"""
from rest_framework import serializers
from .models import ExpertResponse, PairwiseValue, ExpertTypology
from .parser import BLOCK_SIZE


class PairwiseValueSerializer(serializers.Serializer):
    block = serializers.ChoiceField(choices=list(BLOCK_SIZE.keys()))
    i = serializers.IntegerField(min_value=0)
    j = serializers.IntegerField(min_value=0)
    value = serializers.FloatField()

    def validate(self, data):
        n = BLOCK_SIZE[data["block"]]
        if not (0 <= data["i"] < data["j"] < n):
            raise serializers.ValidationError(
                f"Indeks tidak valid untuk blok {data['block']} (n={n}): "
                f"harus 0 <= i < j < {n}."
            )
        v = data["value"]
        if v == 0 or abs(v) > 9 or (abs(v) < 1):
            raise serializers.ValidationError(
                "Nilai harus pada skala Saaty bertanda ±1..±9 (bukan 0)."
            )
        return data


class SubmitResponseSerializer(serializers.Serializer):
    """Payload submit satu ahli: identitas + daftar 26 nilai pairwise."""
    expert_id = serializers.CharField(max_length=64)
    nama = serializers.CharField(max_length=200, allow_blank=True, required=False)
    instansi = serializers.CharField(max_length=200, allow_blank=True, required=False)
    tipologi = serializers.ChoiceField(choices=ExpertTypology.values)
    pairwise = PairwiseValueSerializer(many=True)

    def validate_pairwise(self, items):
        seen = {(it["block"], it["i"], it["j"]) for it in items}
        if len(seen) != len(items):
            raise serializers.ValidationError("Ada perbandingan duplikat.")
        return items


class ExpertResponseSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertResponse
        fields = ["expert_id", "nama", "instansi", "tipologi",
                  "is_valid", "submitted_at", "catatan_validasi"]
