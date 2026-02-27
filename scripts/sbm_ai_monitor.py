#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

# -----------------------------
# Helpers (hashing / formatting)
# -----------------------------

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

def ensure_unique_outdir(out_dir: str) -> str:
    if not os.path.exists(out_dir):
        return out_dir
    if not os.path.isdir(out_dir):
        raise ValueError("out path exists and is not a directory")
    existing = set(os.listdir(out_dir))
    if len(existing) == 0:
        return out_dir
    i = 1
    while True:
        cand = f"{out_dir}_R{i}"
        if not os.path.exists(cand):
            return cand
        i += 1

# -----------------------------
# Core config
# -----------------------------

@dataclass(frozen=True)
class AIMConfig:
    N: int
    H: int
    M: int
    seed: int
    # LCG params (used in lcg mode)
    a1: int
    c1: int
    a2: int
    c2: int
    # shift + fracture gate
    shift_n: int
    long_stable_L: int
    # observation mapping
    obs: str
    # stream modes
    pre_mode: str
    post_mode: str

# -----------------------------
# Deterministic stream + obs
# -----------------------------

def parity_bit(x: int) -> int:
    return 1 if (x & 1) else 0

def popcnt32(x: int) -> int:
    # deterministic popcount for 32-bit domain
    x &= 0xFFFFFFFF
    # Python 3.8+ has int.bit_count()
    return x.bit_count()

def lcg_step(x: int, a: int, c: int, M: int) -> int:
    return (a * x + c) % M

def stream_step(x: int, t: int, mode: str, a: int, c: int, M: int) -> int:
    # pre/post mode can differ. Keep it deterministic.
    if mode == "lcg":
        return lcg_step(x, a, c, M)
    if mode == "plateau":
        # constant plateau: no change
        return x
    if mode == "ramp":
        # deterministic drift independent of x (still deterministic)
        # use t to move linearly; keep in [0,M)
        return (x + (t + 1)) % M
    raise ValueError("Unknown mode")

def build_stream(cfg: AIMConfig) -> List[int]:
    # Need N windows, each window reads H transitions -> need N+H+1 states
    T = cfg.N + cfg.H + 1
    xs = [0] * T
    xs[0] = cfg.seed % cfg.M
    for t in range(0, T - 1):
        if t < cfg.shift_n:
            xs[t + 1] = stream_step(xs[t], t, cfg.pre_mode, cfg.a1, cfg.c1, cfg.M)
        else:
            xs[t + 1] = stream_step(xs[t], t, cfg.post_mode, cfg.a2, cfg.c2, cfg.M)
    return xs

def obs_bit(x0: int, x1: int, cfg: AIMConfig) -> int:
    if cfg.obs == "delta_parity":
        d = (x1 - x0) % cfg.M
        return parity_bit(d)
    if cfg.obs == "xor_parity":
        return parity_bit((x0 ^ x1) & 0xFFFFFFFF)
    if cfg.obs == "x_lsb":
        return parity_bit(x0 & 1)
    if cfg.obs == "popcnt_parity":
        # parity of popcount of xor delta (32-bit)
        return parity_bit(popcnt32((x0 ^ x1) & 0xFFFFFFFF))
    raise ValueError("Unknown obs")

def signature_at(n: int, xs: List[int], cfg: AIMConfig) -> Tuple[int, ...]:
    sig: List[int] = []
    for k in range(cfg.H):
        x0 = xs[n + k]
        x1 = xs[n + k + 1]
        sig.append(obs_bit(x0, x1, cfg))
    return tuple(sig)

# -----------------------------
# Metrics
# -----------------------------

def compute_fracture_metrics(alpha_series: List[Tuple[int, int, int]], cfg: AIMConfig) -> Dict[str, object]:
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

    alpha_before = 0
    alpha_at_shift = 0
    alpha_after = 0
    if alpha_series:
        for (n, a, _newf) in alpha_series:
            if n == cfg.shift_n - 1:
                alpha_before = a
            if n == cfg.shift_n:
                alpha_at_shift = a
            if n == cfg.N - 1:
                alpha_after = a
        if cfg.shift_n - 1 < 0:
            alpha_before = 0

    d_alpha: List[int] = []
    prev = 0
    for (_n, a, _newf) in alpha_series:
        d_alpha.append(a - prev)
        prev = a

    max_spike = 0
    spike_at_n = 0
    stable_run = 0
    max_stable_run = 0
    fracture_candidate = 0
    fracture_at_n = 0

    for i, da in enumerate(d_alpha):
        n = i
        if da == 0:
            stable_run += 1
            if stable_run > max_stable_run:
                max_stable_run = stable_run
        else:
            if da > max_spike:
                max_spike = da
                spike_at_n = n
            if stable_run >= cfg.long_stable_L and da >= 1:
                fracture_candidate += 1
                if fracture_at_n == 0:
                    fracture_at_n = n
            stable_run = 0

    return {
        "N": cfg.N,
        "H": cfg.H,
        "M": cfg.M,
        "seed": cfg.seed,
        "a1": cfg.a1, "c1": cfg.c1,
        "a2": cfg.a2, "c2": cfg.c2,
        "shift_n": cfg.shift_n,
        "obs": cfg.obs,
        "pre_mode": cfg.pre_mode,
        "post_mode": cfg.post_mode,
        "alpha_N": alpha_N,
        "E_N": E_N,
        "Hs_N": Hs_N,
        "C_N": C_N,
        "emergence_count": emergence_count,
        "last_emergence_n": last_emergence_n,
        "mean_gap": mean_gap,
        "var_gap": var_gap,
        "alpha_before_shift": alpha_before,
        "alpha_at_shift": alpha_at_shift,
        "alpha_after": alpha_after,
        "max_stable_run": max_stable_run,
        "max_spike": max_spike,
        "spike_at_n": spike_at_n,
        "fracture_candidate_count": fracture_candidate,
        "fracture_first_at_n": fracture_at_n,
        "long_stable_L": cfg.long_stable_L,
    }

def write_metrics_csv(m: Dict[str, object], out_path: str) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        keys = [
            "N","H","M","seed","shift_n","obs","pre_mode","post_mode",
            "a1","c1","a2","c2",
            "alpha_N","E_N","Hs_N","C_N",
            "emergence_count","last_emergence_n","mean_gap","var_gap",
            "alpha_before_shift","alpha_at_shift","alpha_after",
            "max_stable_run","max_spike","spike_at_n",
            "fracture_candidate_count","fracture_first_at_n",
            "long_stable_L"
        ]
        for k in keys:
            v = m[k]
            if isinstance(v, float):
                w.writerow([k, fmt12(v)])
            else:
                w.writerow([k, str(v)])

def write_profile_json(m: Dict[str, object], out_path: str) -> None:
    prof = {
        "sbm_ai_version": "1.2",
        "N": m["N"],
        "H": m["H"],
        "M": m["M"],
        "seed": m["seed"],
        "shift_n": m["shift_n"],
        "obs": m["obs"],
        "pre_mode": m["pre_mode"],
        "post_mode": m["post_mode"],
        "params_pre": {"a": m["a1"], "c": m["c1"]},
        "params_post": {"a": m["a2"], "c": m["c2"]},
        "profile": {
            "alpha_N": m["alpha_N"],
            "E_N": float(fmt12(float(m["E_N"]))),
            "Hs_N": float(fmt12(float(m["Hs_N"]))),
            "C_N": float(fmt12(float(m["C_N"]))),
            "emergence_count": m["emergence_count"],
            "last_emergence_n": m["last_emergence_n"],
            "mean_gap": float(fmt12(float(m["mean_gap"]))),
            "var_gap": float(fmt12(float(m["var_gap"]))),
            "alpha_before_shift": m["alpha_before_shift"],
            "alpha_at_shift": m["alpha_at_shift"],
            "alpha_after": m["alpha_after"],
            "max_stable_run": m["max_stable_run"],
            "max_spike": m["max_spike"],
            "spike_at_n": m["spike_at_n"],
            "fracture_candidate_count": m["fracture_candidate_count"],
            "fracture_first_at_n": m["fracture_first_at_n"],
            "long_stable_L": m["long_stable_L"],
        },
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(prof, f, ensure_ascii=True, indent=2, sort_keys=False)
        f.write("\n")

# -----------------------------
# Main run
# -----------------------------

def run(cfg: AIMConfig, out_dir: str) -> str:
    out_dir2 = ensure_unique_outdir(out_dir)
    os.makedirs(out_dir2, exist_ok=True)

    results_path  = os.path.join(out_dir2, "sbm_ai_results.csv")
    alpha_path    = os.path.join(out_dir2, "sbm_ai_alphabet.csv")
    metrics_path  = os.path.join(out_dir2, "sbm_ai_metrics.csv")
    profile_path  = os.path.join(out_dir2, "sbm_ai_profile.json")
    manifest_path = os.path.join(out_dir2, "sbm_ai_manifest.sha256")

    xs = build_stream(cfg)

    alphabet: Dict[Tuple[int, ...], int] = {}
    alpha_series: List[Tuple[int, int, int]] = []

    # Full results
    with open(results_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "signature", "new_signature_at_n", "first_seen_n"])
        for n in range(0, cfg.N):
            sig = signature_at(n, xs, cfg)
            if sig not in alphabet:
                alphabet[sig] = n
                new_flag = 1
            else:
                new_flag = 0
            w.writerow([n, repr(sig), new_flag, alphabet[sig]])
            alpha_series.append((n, len(alphabet), new_flag))

    # Alphabet checkpoints (lightweight)
    checkpoints = [
        100, 200, 500, 1000, 2000, 5000,
        10000, 20000, 50000, 100000,
        cfg.shift_n - 1, cfg.shift_n, cfg.N - 1
    ]
    checkpoints = sorted(set([c for c in checkpoints if 0 <= c <= cfg.N - 1]))

    idx_map = {n: distinct for (n, distinct, _new) in alpha_series}
    with open(alpha_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "distinct_signatures_alpha(n)"])
        for c in checkpoints:
            w.writerow([c, idx_map[c]])

    # Metrics + profile + manifest
    m = compute_fracture_metrics(alpha_series, cfg)
    write_metrics_csv(m, metrics_path)
    write_profile_json(m, profile_path)
    write_manifest([results_path, alpha_path, metrics_path, profile_path], manifest_path)

    return out_dir2

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--H", type=int, default=18)
    ap.add_argument("--M", type=int, default=4294967296)
    ap.add_argument("--seed", type=int, default=123456789)

    ap.add_argument("--a1", type=int, default=1664525)
    ap.add_argument("--c1", type=int, default=1013904223)
    ap.add_argument("--a2", type=int, default=22695477)
    ap.add_argument("--c2", type=int, default=1)

    ap.add_argument("--shift_n", type=int, default=-1)
    ap.add_argument("--long_stable_L", type=int, default=2000)

    ap.add_argument("--pre_mode", default="lcg", choices=["lcg", "plateau", "ramp"])
    ap.add_argument("--post_mode", default="lcg", choices=["lcg", "plateau", "ramp"])

    ap.add_argument(
        "--obs",
        default="xor_parity",
        choices=["xor_parity", "delta_parity", "x_lsb", "popcnt_parity"]
    )
    ap.add_argument("--out", default="OUT_SBM_AI")

    args = ap.parse_args()

    shift_n = args.shift_n
    if shift_n < 0:
        shift_n = args.N // 2
    if shift_n < 0:
        shift_n = 0
    if shift_n > args.N - 1:
        shift_n = args.N - 1

    cfg = AIMConfig(
        N=args.N,
        H=args.H,
        M=args.M,
        seed=args.seed,
        a1=args.a1,
        c1=args.c1,
        a2=args.a2,
        c2=args.c2,
        shift_n=shift_n,
        long_stable_L=args.long_stable_L,
        obs=args.obs,
        pre_mode=args.pre_mode,
        post_mode=args.post_mode,
    )

    out_dir2 = run(cfg, args.out)

    print("DONE")
    print(f"OUT DIR: {out_dir2}")
    print("FILES:")
    print(" - sbm_ai_results.csv")
    print(" - sbm_ai_alphabet.csv")
    print(" - sbm_ai_metrics.csv")
    print(" - sbm_ai_profile.json")
    print(" - sbm_ai_manifest.sha256")

if __name__ == "__main__":
    main()