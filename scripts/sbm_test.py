#!/usr/bin/env python3
import argparse
import csv
import hashlib
import math
import os
import json
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_manifest(paths: List[str], out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        for p in paths:
            f.write(f"{sha256_file(p)}  {os.path.basename(p)}\n")

def fmt12(x: float) -> str:
    return f"{x:.12f}"

# =========================
# SBM: Operators + Signatures
# =========================

@dataclass(frozen=True)
class SBMConfig:
    op: str
    H: int
    N: int
    bands: Tuple[int, int, int, int]

def d_min(n: int) -> int:
    if n <= 3:
        return 0 if n in (2, 3) else 2
    r = int(math.isqrt(n))
    for d in range(2, r + 1):
        if n % d == 0:
            return d
    return 0

def band_from_dmin(d: int, thresholds: Tuple[int, int, int, int]) -> str:
    if d == 0:
        return "P"
    t1, t2, t3, t4 = thresholds
    if d <= t1:
        return "A"
    if d <= t2:
        return "B"
    if d <= t3:
        return "C"
    if d <= t4:
        return "D"
    return "E"

def bucket01(x: float, k: int) -> int:
    if k <= 1:
        return 0
    if x < 0.0:
        x = 0.0
    if x > 1.0:
        x = 1.0
    eps = 1e-12
    return int((x - eps) * k) if x > 0.0 else 0

def op_ssnt_signature(n: int, cfg: SBMConfig) -> Tuple[str, int]:
    d = d_min(n)
    b = band_from_dmin(d, cfg.bands)
    if d == 0:
        return (b, 0)
    hn = d / math.sqrt(n)
    hardness_bucket = bucket01(hn, cfg.H)
    return (b, hardness_bucket)

def op_collatz_parity_signature(n: int, cfg: SBMConfig) -> Tuple[int, ...]:
    x = n
    sig: List[int] = []
    for _ in range(cfg.H):
        sig.append(1 if (x & 1) else 0)
        if x & 1:
            x = 3 * x + 1
        else:
            x //= 2
    return tuple(sig)

def op_xorshift_parity_signature(n: int, cfg: SBMConfig) -> Tuple[int, ...]:
    x = n & 0xFFFFFFFF
    sig: List[int] = []
    for _ in range(cfg.H):
        sig.append(1 if (x & 1) else 0)
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17) & 0xFFFFFFFF
        x ^= (x << 5) & 0xFFFFFFFF
        x &= 0xFFFFFFFF
    return tuple(sig)

def op_digitsum_mod9_signature(n: int, cfg: SBMConfig) -> Tuple[int, ...]:
    def sdig(x: int) -> int:
        s = 0
        while x:
            s += x % 10
            x //= 10
        return s

    x = n
    sig: List[int] = []
    for _ in range(cfg.H):
        sig.append(x % 9)
        x = sdig(x)
    return tuple(sig)

def op_sha1_parity_signature(n: int, cfg: SBMConfig) -> Tuple[int, ...]:
    x = n & 0xFFFFFFFF
    sig: List[int] = []
    for _ in range(cfg.H):
        sig.append(1 if (x & 1) else 0)
        h = hashlib.sha1(x.to_bytes(4, byteorder="big")).digest()
        x = int.from_bytes(h[:4], byteorder="big") & 0xFFFFFFFF
    return tuple(sig)

def get_signature_fn(op: str) -> Callable[[int, SBMConfig], Tuple]:
    if op == "ssnt_closure":
        return op_ssnt_signature
    if op == "collatz_parity":
        return op_collatz_parity_signature
    if op == "xorshift_parity":
        return op_xorshift_parity_signature
    if op == "digitsum_mod9":
        return op_digitsum_mod9_signature
    if op == "sha1_parity":
        return op_sha1_parity_signature
    raise ValueError(f"Unknown op: {op}")

# =========================
# Metrics + Profile (SBM v2.0)
# =========================

def compute_metrics(cfg: SBMConfig, alpha_series: List[Tuple[int, int, int]]) -> Dict[str, object]:
    alpha_N = alpha_series[-1][1] if alpha_series else 0
    emergence_indices: List[int] = [n for (n, _a, newf) in alpha_series if newf == 1]
    emergence_count = len(emergence_indices)
    last_emergence_n = emergence_indices[-1] if emergence_count > 0 else 0
    E_N = (emergence_count / float(cfg.N)) if cfg.N > 0 else 0.0
    Hs_N = math.log(alpha_N + 1.0)
    C_N = (Hs_N / math.log(cfg.N)) if cfg.N > 1 else 0.0

    gaps: List[int] = []
    if emergence_count >= 2:
        for i in range(emergence_count - 1):
            gaps.append(emergence_indices[i + 1] - emergence_indices[i])

    if len(gaps) == 0:
        mean_gap = 0.0
        var_gap = 0.0
    else:
        mean_gap = sum(gaps) / float(len(gaps))
        if len(gaps) == 1:
            var_gap = 0.0
        else:
            mu = mean_gap
            var_gap = sum((g - mu) ** 2 for g in gaps) / float(len(gaps))

    return {
        "op": cfg.op,
        "N": cfg.N,
        "H": cfg.H,
        "alpha_N": alpha_N,
        "E_N": E_N,
        "Hs_N": Hs_N,
        "C_N": C_N,
        "emergence_count": emergence_count,
        "last_emergence_n": last_emergence_n,
        "mean_gap": mean_gap,
        "var_gap": var_gap,
        "bands": {"t1": cfg.bands[0], "t2": cfg.bands[1], "t3": cfg.bands[2], "t4": cfg.bands[3]},
    }

def write_metrics_csv(metrics: Dict[str, object], out_path: str) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        for k in ["op", "N", "H", "alpha_N", "E_N", "Hs_N", "C_N",
                  "emergence_count", "last_emergence_n",
                  "mean_gap", "var_gap"]:
            v = metrics[k]
            if isinstance(v, float):
                w.writerow([k, fmt12(v)])
            else:
                w.writerow([k, str(v)])

def write_profile_json(metrics: Dict[str, object], out_path: str) -> None:
    prof = {
        "sbm_version": "2.0",
        "op": metrics["op"],
        "N": metrics["N"],
        "H": metrics["H"],
        "bands": metrics["bands"],
        "profile": {
            "alpha_N": metrics["alpha_N"],
            "E_N": float(fmt12(metrics["E_N"])),
            "Hs_N": float(fmt12(metrics["Hs_N"])),
            "C_N": float(fmt12(metrics["C_N"])),
            "emergence_count": metrics["emergence_count"],
            "last_emergence_n": metrics["last_emergence_n"],
            "mean_gap": float(fmt12(metrics["mean_gap"])),
            "var_gap": float(fmt12(metrics["var_gap"])),
        },
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(prof, f, ensure_ascii=True, indent=2, sort_keys=False)
        f.write("\n")

def run(cfg: SBMConfig, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    sig_fn = get_signature_fn(cfg.op)

    results_path = os.path.join(out_dir, "sbm_results.csv")
    alpha_path = os.path.join(out_dir, "sbm_alphabet.csv")
    metrics_path = os.path.join(out_dir, "sbm_metrics.csv")
    profile_path = os.path.join(out_dir, "sbm_profile.json")
    manifest_path = os.path.join(out_dir, "sbm_manifest.sha256")

    alphabet: Dict[Tuple, int] = {}
    alpha_series: List[Tuple[int, int, int]] = []

    with open(results_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "signature", "new_signature_at_n", "first_seen_n"])
        for n in range(2, cfg.N + 1):
            sig = sig_fn(n, cfg)
            if sig not in alphabet:
                alphabet[sig] = n
                new_flag = 1
            else:
                new_flag = 0
            w.writerow([n, repr(sig), new_flag, alphabet[sig]])
            alpha_series.append((n, len(alphabet), new_flag))

    checkpoints = [
        100, 200, 500, 1000, 2000, 5000,
        10000, 20000, 50000, 100000, cfg.N
    ]
    checkpoints = sorted(set([c for c in checkpoints if 2 <= c <= cfg.N]))

    with open(alpha_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "distinct_signatures_alpha(n)"])
        idx_map = {n: distinct for (n, distinct, _new) in alpha_series}
        for c in checkpoints:
            w.writerow([c, idx_map[c]])

    metrics = compute_metrics(cfg, alpha_series)
    write_metrics_csv(metrics, metrics_path)
    write_profile_json(metrics, profile_path)
    write_manifest([results_path, alpha_path, metrics_path, profile_path], manifest_path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--op", required=True,
        choices=["ssnt_closure", "collatz_parity", "xorshift_parity",
                 "digitsum_mod9", "sha1_parity"])
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--H", type=int, default=10)
    ap.add_argument("--out", default="OUT_SBM")
    ap.add_argument("--t1", type=int, default=3)
    ap.add_argument("--t2", type=int, default=11)
    ap.add_argument("--t3", type=int, default=31)
    ap.add_argument("--t4", type=int, default=101)
    args = ap.parse_args()

    cfg = SBMConfig(
        op=args.op,
        H=args.H,
        N=args.N,
        bands=(args.t1, args.t2, args.t3, args.t4),
    )

    run(cfg, args.out)

    print("DONE")
    print(f"OUT DIR: {args.out}")
    print("FILES:")
    print(" - sbm_results.csv")
    print(" - sbm_alphabet.csv")
    print(" - sbm_metrics.csv")
    print(" - sbm_profile.json")
    print(" - sbm_manifest.sha256")

if __name__ == "__main__":
    main()