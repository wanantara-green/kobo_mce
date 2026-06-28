"""
models.py — Model Django untuk menyimpan respons pairwise AHP dari KoboToolbox.

Skema penyimpanan mengikuti konvensi Tahap 1:
    - 1 ExpertResponse = 1 ahli mengisi seluruh instrumen (26 perbandingan)
    - PairwiseValue menyimpan tiap sel: blok matriks + indeks (i,j) + nilai bertanda
Nilai bertanda: >0 elemen-i lebih penting, <0 elemen-j lebih penting (lihat ahp.py).
"""

from django.db import models


class ExpertTypology(models.TextChoices):
    """4 tipologi ahli FOLUR."""
    AKADEMISI = "akademisi", "Akademisi/Peneliti"
    PEMERINTAH = "pemerintah", "Pemerintah/OPD"
    PRAKTISI = "praktisi", "Praktisi/Penyuluh"
    MASYARAKAT = "masyarakat", "Tokoh Masyarakat/Petani"


class MatrixBlock(models.TextChoices):
    """Blok matriks dalam hierarki AHP."""
    KONSTRUK = "konstruk", "Antar Konstruk (5x5)"
    K1 = "k1", "Indikator Kesesuaian Lahan (2x2)"
    K2 = "k2", "Indikator Daya Dukung Lingkungan (3x3)"
    K3 = "k3", "Indikator Risiko Iklim & Bencana (3x3)"
    K4 = "k4", "Indikator Nilai Konservasi (3x3)"
    K5 = "k5", "Indikator Faktor Sosial-Ekonomi (4x4)"


# Ukuran tiap blok matriks (untuk validasi & rekonstruksi)
BLOCK_SIZE = {"konstruk": 5, "k1": 2, "k2": 3, "k3": 3, "k4": 3, "k5": 4}


class ExpertResponse(models.Model):
    """Satu sesi pengisian instrumen oleh satu ahli."""
    expert_id = models.CharField(max_length=64, unique=True,
                                 help_text="ID unik ahli (mis. dari Kobo _uuid).")
    nama = models.CharField(max_length=200, blank=True)
    instansi = models.CharField(max_length=200, blank=True)
    tipologi = models.CharField(max_length=20, choices=ExpertTypology.choices)
    kobo_submission_id = models.CharField(max_length=64, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True,
                                   help_text="False jika ada matriks tidak konsisten (CR>0.10).")
    catatan_validasi = models.JSONField(default=dict, blank=True,
                                        help_text="Hasil cek CR per blok.")

    class Meta:
        ordering = ["tipologi", "expert_id"]

    def __str__(self):
        return f"{self.expert_id} [{self.tipologi}]"


class PairwiseValue(models.Model):
    """Satu nilai perbandingan berpasangan (satu sel segitiga atas)."""
    response = models.ForeignKey(ExpertResponse, on_delete=models.CASCADE,
                                 related_name="pairwise_values")
    block = models.CharField(max_length=20, choices=MatrixBlock.choices)
    i = models.PositiveSmallIntegerField(help_text="Indeks elemen-i (0-based).")
    j = models.PositiveSmallIntegerField(help_text="Indeks elemen-j (0-based, j>i).")
    value = models.FloatField(help_text="Nilai bertanda ±1..±9 (skala Saaty).")

    class Meta:
        unique_together = ("response", "block", "i", "j")
        ordering = ["block", "i", "j"]

    def __str__(self):
        return f"{self.response.expert_id}:{self.block}[{self.i},{self.j}]={self.value}"
