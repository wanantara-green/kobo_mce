# Stack AHP-MCE — Pembobotan Zonasi

Stack lengkap untuk pengumpulan penilaian ahli (pairwise AHP), perhitungan bobot
deterministik, dan pelaporan agregat — siap dijalankan dengan satu perintah Docker Compose.

```
┌──────────────┐     /api/ proxy    ┌──────────────┐     psql     ┌────────────┐
│  frontend    │ ─────────────────▶│   backend    │ ───────────▶ │     db     │
│ nginx +      │                    │ Django + DRF │              │ PostgreSQL │
│ Tailwind UI  │ ◀─────────────────│ kobo_mce AHP │ ◀─────────── │            │
└──────────────┘                    └──────────────┘              └────────────┘
   :8080                                :8000 (internal)              :5432 (internal)
```

## Menjalankan

```bash
cp .env.example .env        # sesuaikan password & secret
docker compose up --build
```

Lalu buka:
- **http://localhost:8080** — antarmuka penilaian ahli (26 perbandingan pairwise)
- **http://localhost:8080/hasil.html** — dashboard hasil agregat
- **http://localhost:8080/admin/** — Django admin (audit data; buat superuser dulu)

Membuat superuser admin:
```bash
docker compose exec backend python manage.py createsuperuser
```

## Layanan

| Layanan | Basis | Peran |
|---|---|---|
| `db` | postgres:16-alpine | Penyimpanan respons ahli & nilai pairwise |
| `backend` | python:3.12 + Django/DRF | API AHP: submit, validasi CR, agregasi, narasi AI |
| `frontend` | nginx:1.27-alpine | UI statis Tailwind + proksi `/api/` ke backend |

## Endpoint API

| Metode | Path | Fungsi |
|---|---|---|
| POST | `/api/submit/` | Simpan penilaian satu ahli (+ validasi CR otomatis) |
| GET | `/api/experts/` | Daftar ahli & jumlah per tipologi |
| GET | `/api/weights/` | Bobot global 15 indikator + perbandingan tipologi |
| POST | `/api/validate/` | Cek CR satu set pairwise tanpa menyimpan (feedback real-time) |
| POST | `/api/narrative/` | Narasi interpretasi via Claude API (opsional) |

## Alur pengguna

1. Ahli mengisi identitas + memilih tipologi (4 kategori).
2. Menggeser penanda pada 26 perbandingan berpasangan (skala Saaty −9…+9).
3. Layar tinjauan menampilkan CR tiap kelompok; ahli bisa menyesuaikan.
4. Kirim → tersimpan di PostgreSQL, otomatis ditandai konsisten/tidak.
5. Dashboard `hasil.html` menampilkan bobot global teragregasi.

## Konvensi nilai pairwise (penting)

Geseran slider dikonversi ke nilai bertanda yang dipahami backend:
- Slider ke **kiri** → elemen kiri (i) lebih penting → nilai **positif** (skala Saaty)
- Slider ke **kanan** → elemen kanan (j) lebih penting → nilai **negatif** (→ 1/skala)
- Tengah → 1 (sama penting)

Konvensi ini sudah diverifikasi konsisten ujung-ke-ujung dengan `signed_to_ratio()`
di `kobo_mce/weighting/ahp.py`.

## Lapisan AI (opsional)

Isi `ANTHROPIC_API_KEY` di `.env` untuk mengaktifkan endpoint `/api/narrative/`.
Bila kosong, endpoint mengembalikan 503 dan fitur narasi nonaktif — bagian
perhitungan bobot tetap berjalan penuh tanpa API key (bobot bersifat deterministik;
AI hanya untuk interpretasi naratif, tidak pernah mengubah angka).

## Produksi

- Set `DJANGO_DEBUG=0` (default) → backend memakai gunicorn 3 worker.
- Ganti `DJANGO_SECRET_KEY` dan `POSTGRES_PASSWORD` dengan nilai acak.
- Frontend dan API satu origin (via proksi nginx), jadi tidak ada masalah CORS.
- Untuk pengembangan lokal cepat: set `DJANGO_DEBUG=1` → runserver dengan auto-reload.

## Struktur direktori

```
stack/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile  ·  entrypoint.sh  ·  requirements.txt  ·  manage.py
│   ├── ahp_mce/            # proyek Django (settings, urls, wsgi)
│   └── kobo_mce/           # app AHP
│       ├── weighting/      # ahp.py, aggregate.py  (inti deterministik)
│       ├── services/       # mce_pipeline.py
│       ├── models.py  ·  parser.py  ·  serializers.py  ·  views.py
│       ├── api_urls.py  ·  admin.py  ·  ai_layer.py
│       └── migrations/
└── frontend/
    ├── Dockerfile
    ├── nginx/default.conf
    └── static/
        ├── index.html      # form penilaian pairwise
        ├── hasil.html      # dashboard hasil agregat
        ├── config.js       # struktur hierarki (cermin backend)
        └── app.js          # logika interaksi + validasi live
```
