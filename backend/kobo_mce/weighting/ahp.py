"""
ahp.py — Modul inti Analytic Hierarchy Process untuk pipeline MCE FOLUR Luwu.

Fungsi murni (tanpa dependensi Django) agar mudah diuji terpisah.
Konvensi nilai pairwise bertanda:
    nilai > 0  -> elemen-i lebih penting, a[i,j] = nilai (skala Saaty 1..9)
    nilai < 0  -> elemen-j lebih penting, a[i,j] = 1/|nilai|
    nilai == 1 -> sama penting
Resiprokal a[j,i] = 1/a[i,j] diisi otomatis.

Referensi: Saaty (1980); RI dari Saaty's Random Index table.
"""

from __future__ import annotations
import numpy as np

# Random Index (Saaty) untuk n = 1..10
RANDOM_INDEX = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
}

CR_THRESHOLD = 0.10


def signed_to_ratio(value: float) -> float:
    """Konversi satu nilai pairwise bertanda menjadi rasio Saaty positif."""
    v = float(value)
    if v == 0:
        raise ValueError("Nilai pairwise tidak boleh 0; gunakan 1 untuk 'sama penting'.")
    if v >= 1:
        return v
    if v <= -1:
        return 1.0 / abs(v)
    # nilai pecahan antara -1..1 dianggap input tidak valid untuk skala Saaty
    raise ValueError(f"Nilai pairwise tidak valid: {value}. Gunakan ±1..±9.")


def build_matrix(n: int, pairs: dict[tuple[int, int], float]) -> np.ndarray:
    """
    Bangun matriks perbandingan berpasangan n x n.

    pairs: dict {(i, j): nilai_bertanda} untuk i < j (indeks berbasis 0).
    Sel diagonal = 1; sel bawah = resiprokal otomatis.
    """
    M = np.ones((n, n), dtype=float)
    for (i, j), val in pairs.items():
        if not (0 <= i < n and 0 <= j < n):
            raise IndexError(f"Indeks ({i},{j}) di luar ukuran matriks {n}.")
        if i >= j:
            raise ValueError(f"Hanya isi segitiga atas (i<j); diterima ({i},{j}).")
        r = signed_to_ratio(val)
        M[i, j] = r
        M[j, i] = 1.0 / r
    return M


def priority_vector(M: np.ndarray) -> np.ndarray:
    """
    Hitung priority vector (bobot lokal) via eigenvector utama.
    Menggunakan eigenvector dari eigenvalue real terbesar, lalu normalisasi.
    """
    eigvals, eigvecs = np.linalg.eig(M)
    idx = int(np.argmax(eigvals.real))
    w = np.abs(eigvecs[:, idx].real)
    return w / w.sum()


def consistency_ratio(M: np.ndarray) -> dict:
    """
    Hitung lambda_max, Consistency Index (CI), dan Consistency Ratio (CR).
    Untuk n <= 2, CR = 0 (selalu konsisten).
    """
    n = M.shape[0]
    w = priority_vector(M)
    if n <= 2:
        return {"n": n, "lambda_max": float(n), "CI": 0.0, "CR": 0.0,
                "consistent": True, "priority": w}
    # lambda_max via rata-rata (M w)/w
    Mw = M @ w
    lambda_max = float((Mw / w).mean())
    CI = (lambda_max - n) / (n - 1)
    RI = RANDOM_INDEX.get(n)
    if RI is None or RI == 0:
        CR = 0.0
    else:
        CR = CI / RI
    return {
        "n": n,
        "lambda_max": lambda_max,
        "CI": CI,
        "CR": CR,
        "consistent": CR <= CR_THRESHOLD,
        "priority": w,
    }


def evaluate(n: int, pairs: dict[tuple[int, int], float]) -> dict:
    """Pipeline ringkas: bangun matriks -> priority + CR."""
    M = build_matrix(n, pairs)
    res = consistency_ratio(M)
    res["matrix"] = M
    return res


if __name__ == "__main__":
    # Contoh uji cepat: matriks 5x5 antar konstruk (data dummy konsisten)
    demo_pairs = {
        (0, 1): 2, (0, 2): 3, (0, 3): 2, (0, 4): 4,
        (1, 2): 2, (1, 3): 1, (1, 4): 3,
        (2, 3): -2, (2, 4): 2,
        (3, 4): 3,
    }
    out = evaluate(5, demo_pairs)
    np.set_printoptions(precision=4, suppress=True)
    print("Priority vector :", out["priority"])
    print("lambda_max      :", round(out["lambda_max"], 4))
    print("CI              :", round(out["CI"], 4))
    print("CR              :", round(out["CR"], 4),
          "->", "KONSISTEN" if out["consistent"] else "TIDAK KONSISTEN (revisi)")
