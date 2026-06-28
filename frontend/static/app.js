// app.js — Form AHP-MCE satu halaman: seluruh perbandingan tampil sekaligus,
// dikelompokkan per blok, dengan CR per kelompok yang diperbarui langsung.

const state = {
  nama: "", instansi: "", tipologi: "",
  comparisons: buildComparisons(),   // urutan = urutan blok
  values: {},                         // index global -> nilai slider (-9..9)
};
state.comparisons.forEach((_, idx) => { state.values[idx] = 0; });

const $ = (id) => document.getElementById(id);

const BLOCK_LABEL = {
  konstruk: "Antar Kriteria Utama", k1: "Kesesuaian Lahan",
  k2: "Daya Dukung Lingkungan", k3: "Risiko Iklim & Bencana",
  k4: "Nilai Konservasi", k5: "Faktor Sosial-Ekonomi",
};

// ---------- Identitas ----------
function renderTipologi() {
  const wrap = $("tipologi-options");
  wrap.innerHTML = "";
  TIPOLOGI.forEach((t) => {
    const btn = document.createElement("button");
    btn.textContent = t.label;
    btn.className = "tipologi-btn text-sm rounded-xl border border-canopy-800/20 px-3 py-2.5 text-left hover:border-canopy-600 transition-colors";
    btn.onclick = () => {
      state.tipologi = t.value;
      document.querySelectorAll(".tipologi-btn").forEach((b) =>
        b.classList.remove("bg-canopy-700", "text-white", "border-canopy-700"));
      btn.classList.add("bg-canopy-700", "text-white", "border-canopy-700");
      updateSubmitBtn();
    };
    wrap.appendChild(btn);
  });
}

function updateSubmitBtn() {
  state.nama = $("in-nama").value.trim();
  state.instansi = $("in-instansi").value.trim();
  $("btn-submit").disabled = !(state.nama && state.tipologi);
}

// ---------- Slider -> teks ----------
function sliderToVerbal(v) {
  if (v === 0) return "Sama penting";
  const cap = v < 0 ? "Kiri" : "Kanan";
  return `${cap} ${SAATY_VERBAL[Math.abs(v)]}`;
}

// ---------- Render seluruh kelompok ----------
function renderBlocks() {
  const root = $("blocks");
  root.innerHTML = "";

  // Kelompokkan indeks global per blok (urutan comparisons sudah per blok)
  const byBlock = {};
  state.comparisons.forEach((c, idx) => {
    (byBlock[c.block] = byBlock[c.block] || []).push(idx);
  });

  let blockNo = 0;
  for (const block of BLOCK_ORDER) {
    const idxs = byBlock[block];
    if (!idxs) continue;
    blockNo++;

    const section = document.createElement("section");
    section.className = "bg-white/75 border border-canopy-800/12 rounded-2xl shadow-sm mb-6 overflow-hidden";

    // Header kelompok + badge CR
    const head = document.createElement("div");
    head.className = "flex items-center justify-between gap-3 px-5 sm:px-6 py-4 border-b border-canopy-800/10 bg-canopy-50/40";
    head.innerHTML = `
      <div>
        <p class="font-mono text-[11px] text-clay-600">Kelompok ${blockNo} · ${idxs.length} perbandingan</p>
        <h2 class="font-display font-semibold text-lg text-canopy-800">${BLOCK_LABEL[block] || block}</h2>
      </div>
      <div class="text-right">
        <span id="cr-${block}" class="font-mono text-xs rounded-full px-3 py-1 border border-canopy-800/15 text-canopy-700/60">CR —</span>
        <p id="hint-${block}" class="text-[11px] text-clay-600 mt-1 max-w-[15rem] hidden"></p>
      </div>`;
    section.appendChild(head);

    // Baris-baris perbandingan
    const body = document.createElement("div");
    body.className = "divide-y divide-canopy-800/8";
    idxs.forEach((idx) => body.appendChild(renderRow(idx)));
    section.appendChild(body);

    root.appendChild(section);
  }
}

function renderRow(idx) {
  const c = state.comparisons[idx];
  const row = document.createElement("div");
  row.className = "px-5 sm:px-6 py-4";
  row.innerHTML = `
    <div class="grid grid-cols-1 sm:grid-cols-[1fr_minmax(180px,2fr)_1fr] gap-3 sm:gap-4 items-center">
      <div id="card-left-${idx}" class="text-center sm:text-right rounded-lg border-2 border-canopy-800/12 px-3 py-2 transition-all">
        <p class="font-display font-medium leading-snug">${c.left}</p>
      </div>
      <div>
        <input id="slider-${idx}" type="range" min="-9" max="9" step="1" value="${state.values[idx]}"
          class="w-full" aria-label="Perbandingan ${c.left} dengan ${c.right}" />
        <div class="flex justify-between font-mono text-[10px] text-canopy-700/50 mt-1.5 px-0.5">
          <span>← ${c.left}</span><span>seimbang</span><span>${c.right} →</span>
        </div>
        <p id="verbal-${idx}" class="text-center mt-1.5 text-sm text-canopy-800 font-medium min-h-[1.25rem]">${sliderToVerbal(state.values[idx])}</p>
      </div>
      <div id="card-right-${idx}" class="text-center sm:text-left rounded-lg border-2 border-canopy-800/12 px-3 py-2 transition-all">
        <p class="font-display font-medium leading-snug">${c.right}</p>
      </div>
    </div>`;

  // Pasang listener setelah elemen dibuat
  setTimeout(() => {
    const slider = row.querySelector(`#slider-${idx}`);
    slider.addEventListener("input", () => onSliderInput(idx));
    updateRowVisual(idx);
  }, 0);
  return row;
}

function onSliderInput(idx) {
  state.values[idx] = parseInt($(`slider-${idx}`).value, 10);
  updateRowVisual(idx);
  scheduleValidate();
  updateFilledCount();
}

function updateRowVisual(idx) {
  const v = state.values[idx];
  $(`verbal-${idx}`).textContent = sliderToVerbal(v);
  const left = $(`card-left-${idx}`), right = $(`card-right-${idx}`);
  left.className = "text-center sm:text-right rounded-lg border-2 px-3 py-2 transition-all";
  right.className = "text-center sm:text-left rounded-lg border-2 px-3 py-2 transition-all";
  if (v < 0) {
    left.classList.add("border-clay-500", "bg-clay-400/10");
    right.classList.add("border-canopy-800/12");
  } else if (v > 0) {
    right.classList.add("border-canopy-600", "bg-canopy-50");
    left.classList.add("border-canopy-800/12");
  } else {
    left.classList.add("border-canopy-800/12");
    right.classList.add("border-canopy-800/12");
  }
}

// ---------- Konversi nilai -> payload bertanda (sama dgn versi langkah) ----------
function buildPairwisePayload() {
  return state.comparisons.map((c, idx) => {
    const v = state.values[idx];
    let signed;
    if (v === 0) signed = 1;
    else if (v < 0) signed = Math.abs(v);  // kiri (elemen-i) lebih penting
    else signed = -v;                        // kanan (elemen-j) lebih penting
    return { block: c.block, i: c.i, j: c.j, value: signed };
  });
}

// ---------- Validasi CR langsung (debounce) ----------
let validateTimer = null;
function scheduleValidate() {
  clearTimeout(validateTimer);
  validateTimer = setTimeout(runValidate, 400);
}

async function runValidate() {
  try {
    const res = await fetch(`${API_BASE}/validate/`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pairwise: buildPairwisePayload() }),
    });
    const data = await res.json();
    let worst = 0, nBad = 0;
    for (const [block, r] of Object.entries(data.per_block)) {
      const badge = $(`cr-${block}`);
      if (!badge) continue;
      const ok = r.consistent;
      worst = Math.max(worst, r.CR);
      if (!ok) nBad++;
      badge.textContent = `CR ${r.CR.toFixed(3)} · ${ok ? "baik" : "tinggi"}`;
      badge.className = "font-mono text-xs rounded-full px-3 py-1 border " +
        (ok ? "border-canopy-600/40 bg-canopy-50 text-canopy-700"
            : "border-red-600 bg-red-600 text-white");
      // Petunjuk tindakan saat CR tinggi
      const hint = $(`hint-${block}`);
      if (hint) {
        if (ok) { hint.classList.add("hidden"); hint.textContent = ""; }
        else {
          hint.classList.remove("hidden");
          hint.textContent = "⚠ Kurang konsisten — longgarkan 1–2 penilaian paling ekstrem di kelompok ini.";
        }
      }
    }
    const oc = $("overall-cr");
    if (worst <= 0.10) {
      oc.textContent = `CR tertinggi: ${worst.toFixed(3)} · semua kelompok baik ✓`;
      oc.className = "text-canopy-700";
    } else {
      oc.textContent = `CR tertinggi: ${worst.toFixed(3)} · ${nBad} kelompok perlu ditinjau`;
      oc.className = "text-clay-600";
    }
    state._allConsistent = (worst <= 0.10);
  } catch (e) {
    $("overall-cr").textContent = "CR keseluruhan: gagal menghubungi server";
  }
}

function updateFilledCount() {
  const n = Object.values(state.values).filter((v) => v !== 0).length;
  $("filled-count").textContent = `${n} dari ${state.comparisons.length} dinilai tidak seimbang`;
}

// ---------- Atur ulang ----------
function resetAll() {
  if (!confirm("Atur ulang semua slider ke posisi seimbang?")) return;
  state.comparisons.forEach((_, idx) => {
    state.values[idx] = 0;
    const s = $(`slider-${idx}`);
    if (s) { s.value = 0; updateRowVisual(idx); }
  });
  updateFilledCount();
  runValidate();
}

// ---------- Kirim ----------
async function submitAll() {
  const btn = $("btn-submit");

  // Guard konsistensi: ingatkan konsekuensi bila ada kelompok CR > 0,10
  if (state._allConsistent === false) {
    const lanjut = confirm(
      "Sebagian kelompok masih kurang konsisten (CR > 0,10).\n\n" +
      "Respons tetap tersimpan, TETAPI tidak akan ikut dihitung dalam bobot agregat " +
      "sampai semua kelompok konsisten (CR ≤ 0,10).\n\n" +
      "Tekan Batal untuk menyesuaikan dulu, atau OK untuk tetap mengirim."
    );
    if (!lanjut) return;
  }

  const original = btn.textContent;
  btn.disabled = true; btn.textContent = "Mengirim…";
  const expertId = `${state.tipologi}-${Date.now()}`;
  try {
    const res = await fetch(`${API_BASE}/submit/`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        expert_id: expertId, nama: state.nama, instansi: state.instansi,
        tipologi: state.tipologi, pairwise: buildPairwisePayload(),
      }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Gagal mengirim");
    const data = await res.json();
    $("done-msg").textContent = data.is_valid
      ? "Penilaian Anda tersimpan dan dinilai konsisten. Terima kasih atas kontribusinya."
      : "Penilaian Anda tersimpan. Sebagian kelompok kurang konsisten, namun tetap tercatat.";
    $("done-overlay").classList.remove("hidden");
  } catch (e) {
    btn.disabled = false; btn.textContent = original;
    alert("Gagal mengirim: " + e.message);
  }
}

// ---------- Wiring ----------
function init() {
  renderTipologi();
  renderBlocks();
  $("in-nama").addEventListener("input", updateSubmitBtn);
  $("in-instansi").addEventListener("input", updateSubmitBtn);
  $("btn-reset").onclick = resetAll;
  $("btn-submit").onclick = submitAll;
  updateSubmitBtn();
  updateFilledCount();
  runValidate();   // tampilkan CR awal (semua seimbang)
}

document.addEventListener("DOMContentLoaded", init);
