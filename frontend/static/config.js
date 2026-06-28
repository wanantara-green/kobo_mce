// config.js — Struktur hierarki & konfigurasi API (cermin dari backend kobo_mce).

const API_BASE = window.AHP_API_BASE || "/api";

// Urutan & label HARUS sama dengan weighting/aggregate.py
const CONSTRUCTS = [
  { code: "konstruk", short: "K1", label: "Kesesuaian Lahan" },
  { code: "konstruk", short: "K2", label: "Daya Dukung Lingkungan" },
  { code: "konstruk", short: "K3", label: "Risiko Iklim & Bencana" },
  { code: "konstruk", short: "K4", label: "Nilai Konservasi" },
  { code: "konstruk", short: "K5", label: "Faktor Sosial-Ekonomi" },
];

// Elemen tiap blok (untuk membangun label perbandingan)
const BLOCKS = {
  konstruk: {
    title: "Antar Kriteria Utama",
    desc: "Seberapa penting tiap kriteria dibanding yang lain untuk menentukan zonasi.",
    elements: [
      "Kesesuaian Lahan", "Daya Dukung Lingkungan", "Risiko Iklim & Bencana",
      "Nilai Konservasi", "Faktor Sosial-Ekonomi",
    ],
  },
  k1: {
    title: "Indikator — Kesesuaian Lahan",
    desc: "Bobot tiap komoditas dalam kriteria kesesuaian lahan.",
    elements: ["Kesesuaian Kakao", "Kesesuaian Padi",
               "Kesesuaian Lainnya (Jagung, Sagu, Cengkeh)"],
  },
  k2: {
    title: "Indikator — Daya Dukung Lingkungan",
    desc: "Bobot tiap aspek daya dukung lingkungan.",
    elements: ["Daya Dukung Lahan", "Daya Dukung Air", "Kinerja Jasa Ekosistem"],
  },
  k3: {
    title: "Indikator — Risiko Iklim & Bencana",
    desc: "Bobot tiap jenis risiko.",
    elements: ["Risiko Banjir/Longsor", "Risiko Kekeringan", "Risiko Hidrometeorologi"],
  },
  k4: {
    title: "Indikator — Nilai Konservasi",
    desc: "Bobot tiap aspek nilai konservasi.",
    elements: ["Kawasan ABKT", "Area Preservasi", "Fungsi Hidrologi"],
  },
  k5: {
    title: "Indikator — Faktor Sosial-Ekonomi",
    desc: "Bobot tiap faktor sosial-ekonomi.",
    elements: ["Permukiman", "Infrastruktur", "Diversifikasi Komoditas", "Aktivitas Ekonomi"],
  },
};

const BLOCK_ORDER = ["konstruk", "k1", "k2", "k3", "k4", "k5"];

const TIPOLOGI = [
  { value: "akademisi", label: "Akademisi / Peneliti" },
  { value: "pemerintah", label: "Pemerintah / OPD" },
  { value: "praktisi", label: "Praktisi / Penyuluh" },
  { value: "masyarakat", label: "Tokoh Masyarakat / Petani" },
];

// Skala Saaty verbal untuk label slider
const SAATY_VERBAL = {
  1: "sama penting",
  2: "sedikit (lemah)",
  3: "sedikit lebih penting",
  4: "lebih (sedang)",
  5: "lebih penting",
  6: "lebih (kuat)",
  7: "sangat lebih penting",
  8: "sangat (sangat kuat)",
  9: "mutlak lebih penting",
};

// Hasilkan seluruh daftar perbandingan (26) sesuai urutan blok
function buildComparisons() {
  const comps = [];
  for (const block of BLOCK_ORDER) {
    const els = BLOCKS[block].elements;
    for (let i = 0; i < els.length; i++) {
      for (let j = i + 1; j < els.length; j++) {
        comps.push({ block, i, j, left: els[i], right: els[j], blockTitle: BLOCKS[block].title });
      }
    }
  }
  return comps;
}
