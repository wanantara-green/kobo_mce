<<<<<<< HEAD
# ahp-ai
=======
# kobo_mce — Modul Pembobotan AHP untuk Zonasi MCE FOLUR Luwu

Pipeline AHP (Analytic Hierarchy Process) untuk pembobotan multi-indikator pada
analisis MCE-GIS, dirancang untuk panel ahli kecil (n≈15) dengan 5 konstruk dan
15 indikator. Bobot bersifat deterministik dan auditable; lapisan AI hanya
membantu validasi dan narasi, tidak pernah mengubah angka bobot.

## Struktur hierarki

```
GOAL: Bobot Zonasi MCE FOLUR Luwu
├── K1 Kesesuaian Lahan ........ Kesesuaian Kakao, Kesesuaian Padi
├── K2 Daya Dukung Lingkungan .. Daya Dukung Lahan, Daya Dukung Air, Kinerja Jasa Ekosistem
├── K3 Risiko Iklim & Bencana .. Risiko Banjir/Longsor, Risiko Kekeringan, Risiko Hidrometeorologi
├── K4 Nilai Konservasi ........ Kawasan ABKT, Area Preservasi, Fungsi Hidrologi
└── K5 Faktor Sosial-Ekonomi ... Permukiman, Infrastruktur, Diversifikasi Komoditas, Aktivitas Ekonomi
```

Total pairwise per ahli: **26** (10 antar konstruk + 1+3+3+3+6 antar indikator).

## Alur data

```
Kobo submission (JSON)
   │  parser.parse_kobo_submission()
   ▼
ExpertResponse + PairwiseValue  (models.py)
   │  parser.build_matrices_for_response()
   ▼
6 matriks pairwise per ahli  (numpy)
   │  weighting/ahp.py  → priority vector + CR per matriks
   │  weighting/aggregate.py → AIJ geometric-mean grup
   ▼
services/mce_pipeline.run_pipeline()
   │  → bobot global gabungan + per-tipologi
   ▼
export_weights_table() → CSV/JSON siap overlay MCE-GIS
ai_layer.py → validasi anomali, saran perbaikan, narasi (opsional)
```

## File

| File | Isi |
|---|---|
| `weighting/ahp.py` | Inti AHP: build matriks, eigenvector, Consistency Ratio. Tanpa dependensi Django. |
| `weighting/aggregate.py` | Agregasi grup AIJ (geometric-mean), bobot global 15 indikator. |
| `models.py` | Model Django: `ExpertResponse`, `PairwiseValue`. |
| `parser.py` | Parsing payload Kobo + rekonstruksi matriks + validasi CR per ahli. |
| `services/mce_pipeline.py` | Orkestrasi: agregasi gabungan + per-tipologi, ekspor tabel, perbandingan tipologi. |
| `ai_layer.py` | Deteksi anomali konsistensi, saran perbaikan deterministik, narasi via Claude API. |

## Konvensi nilai pairwise

Disimpan bertanda: `>0` = elemen-i lebih penting (skala Saaty 1..9),
`<0` = elemen-j lebih penting (sistem konversi ke 1/skala). `1` = sama penting.
Kolom Kobo: `{block}_{i+1}_{j+1}` mis. `konstruk_1_2`, `k5_3_4`.

## Integrasi ke proyek Django

1. Salin `kobo_mce/` ke root proyek Django.
2. Tambahkan `kobo_mce` ke `INSTALLED_APPS`.
3. `python manage.py makemigrations kobo_mce && python manage.py migrate`.
4. Buat endpoint webhook Kobo yang memanggil `parser.parse_kobo_submission()`
   lalu menyimpan `ExpertResponse` + `PairwiseValue`, dan menandai `is_valid`
   dengan `parser.validate_response()`.
5. Jalankan `services/mce_pipeline.run_pipeline(ExpertResponse.objects.all())`.

## Catatan metodologis

- Geometric mean (bukan aritmetik) dipakai untuk AIJ agar sifat resiprokal
  matriks terjaga — standar AHP grup (Forman & Peniwati, 1998).
- Ambang konsistensi CR ≤ 0.10 (Saaty). Matriks 2×2 (K1) selalu konsisten.
- Ahli dengan matriks tidak konsisten otomatis diekslusi dari agregasi.
- Bobot global = bobot konstruk × bobot indikator lokal, dinormalisasi ke Σ=1.
>>>>>>> master
