import os
import csv
import argparse
from typing import List, Tuple, Optional, Set, Dict


def try_int(x: str) -> Optional[int]:
    try:
        return int(float(x))
    except Exception:
        return None


def safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def find_results_files(root: str) -> List[str]:
    out: List[str] = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower() == "sbm_results.csv":
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def read_results_csv_alpha(path: str) -> Tuple[List[int], List[int], Dict[str, object]]:
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise RuntimeError(f"Empty header in: {path}")

        fields = [k.strip() for k in reader.fieldnames]

        idx_candidates: List[str] = []
        for k in fields:
            lk = k.lower()
            if lk in ("n", "t", "i", "step", "index", "sample_n", "row", "pos"):
                idx_candidates.append(k)
        if not idx_candidates:
            for k in fields:
                lk = k.lower()
                if lk == "n" or "step" in lk or "index" in lk or "sample" in lk:
                    idx_candidates.append(k)

        sig_candidates: List[str] = []
        for k in fields:
            lk = k.lower()
            if lk in ("signature", "sig", "code", "state", "symbol", "sigma", "token"):
                sig_candidates.append(k)
        if not sig_candidates:
            for k in fields:
                lk = k.lower()
                if "signature" in lk or lk.startswith("sig") or "sigma" in lk:
                    sig_candidates.append(k)

        if not idx_candidates or not sig_candidates:
            raise RuntimeError(
                f"Could not locate index/signature columns in {path}. Header: {fields}"
            )

        idx_key = idx_candidates[0]
        sig_key = sig_candidates[0]

        Ns: List[int] = []
        alphas: List[int] = []
        seen: Set[str] = set()
        row_i = 0

        for row in reader:
            row_i += 1
            idx_raw = (row.get(idx_key) or "").strip()
            sig_raw = (row.get(sig_key) or "").strip()

            n_val = try_int(idx_raw)
            if n_val is None:
                n_val = row_i

            if sig_raw != "":
                seen.add(sig_raw)

            Ns.append(n_val)
            alphas.append(len(seen))

        meta: Dict[str, object] = {
            "path": path,
            "idx_key": idx_key,
            "sig_key": sig_key,
            "rows": row_i,
            "alpha_final": alphas[-1] if alphas else 0,
        }
        return Ns, alphas, meta


def filter_emergence_points(Ns: List[int], alphas: List[int]) -> Tuple[List[int], List[int]]:
    if not Ns or not alphas:
        return [], []
    eN = [Ns[0]]
    eA = [alphas[0]]
    last = alphas[0]
    for n, a in zip(Ns[1:], alphas[1:]):
        if a != last:
            eN.append(n)
            eA.append(a)
            last = a
    return eN, eA


def compute_delta_series(Ns: List[int], alphas: List[int]) -> Tuple[List[int], List[int]]:
    if not Ns or not alphas:
        return [], []
    dN: List[int] = []
    dA: List[int] = []
    last = alphas[0]
    for n, a in zip(Ns[1:], alphas[1:]):
        d = a - last
        if d != 0:
            dN.append(n)
            dA.append(d)
        last = a
    return dN, dA


def cap_by_N(Ns: List[int], Ys: List[int], xcap: Optional[int]) -> Tuple[List[int], List[int]]:
    if xcap is None:
        return Ns, Ys
    outN: List[int] = []
    outY: List[int] = []
    for n, y in zip(Ns, Ys):
        if n <= xcap:
            outN.append(n)
            outY.append(y)
        else:
            break
    return outN, outY


def build_label_from_path(p: str, short_labels: bool) -> str:
    parts = os.path.normpath(p).split(os.sep)
    if len(parts) >= 2:
        bundle = parts[-2]
    else:
        bundle = os.path.basename(os.path.dirname(p))
    if short_labels:
        return bundle
    if len(parts) >= 3:
        return "/".join(parts[-3:-1])
    return bundle


def is_primary_replay_pair(label_a: str, label_b: str) -> bool:
    la = label_a.lower()
    lb = label_b.lower()
    if ("primary" in la and "replay" in lb) or ("replay" in la and "primary" in lb):
        return True
    return False


def plot_series_line_step_emergence(
    series: List[Tuple[str, List[int], List[int]]],
    out_png: str,
    title: str,
    mode: str,
    legend_loc: str,
    annotate: bool,
    stamp_text: str,
    stamp_loc: str,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise RuntimeError("matplotlib is required for plotting. Install it and retry.") from e

    plt.figure()

    if mode == "step":
        for label, Ns, Ys in series:
            plt.step(Ns, Ys, where="post", label=label)
    elif mode == "emergence":
        for label, Ns, Ys in series:
            plt.plot(Ns, Ys, marker="o", linestyle="-", label=label)
    else:
        for label, Ns, Ys in series:
            plt.plot(Ns, Ys, label=label)

    plt.xlabel("N")
    plt.ylabel("alpha(N,H)")
    plt.title(title)

    if annotate and stamp_text:
        _apply_stamp(plt, stamp_text, stamp_loc)

    plt.legend(loc=legend_loc)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()


def plot_delta(
    series: List[Tuple[str, List[int], List[int]]],
    out_png: str,
    legend_loc: str,
    annotate: bool,
    stamp_text: str,
    stamp_loc: str,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise RuntimeError("matplotlib is required for plotting. Install it and retry.") from e

    plt.figure()

    for label, Ns, dA in series:
        plt.vlines(Ns, [0] * len(Ns), dA, label=label)

    plt.xlabel("N")
    plt.ylabel("delta_alpha(N,H)")
    plt.title("SBM alpha(N,H) vs N (delta emergence spikes)")

    if annotate and stamp_text:
        _apply_stamp(plt, stamp_text, stamp_loc)

    plt.legend(loc=legend_loc)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()


def _apply_stamp(plt, text: str, stamp_loc: str) -> None:
    loc = (stamp_loc or "lower left").lower().strip()
    if loc == "upper left":
        x, y, va = 0.02, 0.98, "top"
    elif loc == "upper right":
        x, y, va = 0.98, 0.98, "top"
    elif loc == "lower right":
        x, y, va = 0.98, 0.02, "bottom"
    else:
        x, y, va = 0.02, 0.02, "bottom"

    ha = "left" if "left" in loc else "right"
    plt.gca().text(
        x,
        y,
        text,
        transform=plt.gca().transAxes,
        fontsize=10,
        verticalalignment=va,
        horizontalalignment=ha,
        bbox=dict(boxstyle="round", alpha=0.15),
    )


def plot_diff(
    primary: Tuple[str, List[int], List[int]],
    replay: Tuple[str, List[int], List[int]],
    out_png: str,
    xcap: Optional[int],
    annotate: bool,
    stamp_loc: str,
) -> Tuple[int, str]:
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise RuntimeError("matplotlib is required for plotting. Install it and retry.") from e

    label_p, Ns_p, A_p = primary
    label_r, Ns_r, A_r = replay

    mp: Dict[int, int] = {}
    for n, a in zip(Ns_p, A_p):
        mp[n] = a

    difN: List[int] = []
    difY: List[int] = []
    max_abs = 0

    for n, a in zip(Ns_r, A_r):
        if xcap is not None and n > xcap:
            break
        if n in mp:
            d = mp[n] - a
            difN.append(n)
            difY.append(d)
            if abs(d) > max_abs:
                max_abs = abs(d)

    plt.figure()
    plt.plot(difN, difY)
    plt.xlabel("N")
    plt.ylabel("alpha_primary(N,H) - alpha_replay(N,H)")
    plt.title(f"SBM alpha(N,H) vs N (diff: primary - replay) | max_abs_diff={max_abs}")

    stamp_lines = [
        "SBM Proof Plot (viz-only)",
        "mode=diff",
        f"xcap={xcap}" if xcap is not None else "xcap=",
        f"pair_base={_pair_base_from_labels(label_p, label_r)}",
        f"max_abs_diff={max_abs}",
    ]
    if max_abs == 0:
        stamp_lines.append("B_A=B_B (observed)")
    stamp_text = "\n".join(stamp_lines)

    if annotate:
        _apply_stamp(plt, stamp_text, stamp_loc)

    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()
    return max_abs, stamp_text


def _pair_base_from_labels(label_p: str, label_r: str) -> str:
    def strip_suffix(s: str) -> str:
        s2 = s.replace("PRIMARY", "").replace("REPLAY", "")
        s2 = s2.replace("_A_", "_A_").strip("_").strip()
        return s2
    a = strip_suffix(label_p)
    b = strip_suffix(label_r)
    if len(a) <= len(b):
        return a
    return b


def auto_outfile(default_name: str, mode: str, xcap: Optional[int]) -> str:
    name = (default_name or "").strip()
    if not name:
        name = "alpha_curve.png"

    if name.lower() == "alpha_curve.png":
        suffix = mode
        if xcap is not None:
            suffix = f"{suffix}_xcap{xcap}"
        return f"alpha_curve_{suffix}.png"

    return name


def main() -> int:
    ap = argparse.ArgumentParser(
        description="SBM visualization (non-frozen): alpha(N,H) vs N from sbm_results.csv."
    )
    ap.add_argument("--ref_root", default="reference_outputs", help="Root folder containing reference outputs.")
    ap.add_argument("--select", default="", help="Comma-separated substrings to select bundles (optional).")
    ap.add_argument("--outdir", default=os.path.join("viz", "out"), help="Output folder for plots.")
    ap.add_argument("--outfile", default="alpha_curve.png", help="Output PNG filename.")
    ap.add_argument("--title", default="SBM alpha(N,H) vs N", help="Plot title.")
    ap.add_argument(
        "--mode",
        default="step",
        choices=["step", "line", "emergence", "delta", "diff"],
        help="Plot style.",
    )
    ap.add_argument("--xcap", default="", help="Optional cap for N (e.g., 500).")
    ap.add_argument("--collapse_identical", default="1", choices=["0", "1"], help="Collapse identical primary/replay into one series.")
    ap.add_argument("--annotate", default="1", choices=["0", "1"], help="Add stamp box on plot.")
    ap.add_argument("--legend_loc", default="best", help='Legend location (e.g., "upper left"). Use quotes if it contains spaces.')
    ap.add_argument("--stamp_loc", default="lower left", help='Stamp box location (e.g., "lower left"). Use quotes if it contains spaces.')
    ap.add_argument("--short_labels", default="0", choices=["0", "1"], help="Use short labels (bundle-only).")

    args = ap.parse_args()

    if not os.path.isdir(args.ref_root):
        raise RuntimeError(f"Reference root not found: {args.ref_root}")

    files = find_results_files(args.ref_root)
    if not files:
        raise RuntimeError(f"No sbm_results.csv found under: {args.ref_root}")

    selects = [s.strip() for s in args.select.split(",") if s.strip()]
    if selects:
        def keep(p: str) -> bool:
            lp = p.lower()
            return any(sel.lower() in lp for sel in selects)
        files = [p for p in files if keep(p)]
        if not files:
            raise RuntimeError(f"No sbm_results.csv matched selects={selects}")

    xcap_val: Optional[int] = None
    if args.xcap.strip() != "":
        xcap_val = int(args.xcap.strip())

    short_labels = args.short_labels == "1"
    annotate = args.annotate == "1"
    collapse_identical = args.collapse_identical == "1"
    legend_loc = args.legend_loc
    stamp_loc = args.stamp_loc

    raw_series: List[Tuple[str, List[int], List[int], Dict[str, object]]] = []
    for p in files:
        Ns, alphas, meta = read_results_csv_alpha(p)
        label = build_label_from_path(p, short_labels)

        if args.mode == "emergence":
            Ns_use, alphas_use = filter_emergence_points(Ns, alphas)
        elif args.mode == "delta":
            Ns_use, alphas_use = compute_delta_series(Ns, alphas)
        else:
            Ns_use, alphas_use = Ns, alphas

        Ns_use, alphas_use = cap_by_N(Ns_use, alphas_use, xcap_val)
        raw_series.append((label, Ns_use, alphas_use, meta))

    if args.mode == "diff":
        prim_idx = None
        rep_idx = None
        for i, (label, _, _, _) in enumerate(raw_series):
            l = label.lower()
            if "primary" in l:
                prim_idx = i
            if "replay" in l:
                rep_idx = i

        if prim_idx is None or rep_idx is None:
            if len(raw_series) != 2:
                raise RuntimeError("diff mode requires exactly one PRIMARY and one REPLAY series (or exactly two series).")
            prim_idx, rep_idx = 0, 1

        label_p, Ns_p, A_p, meta_p = raw_series[prim_idx]
        label_r, Ns_r, A_r, meta_r = raw_series[rep_idx]

        safe_mkdir(args.outdir)
        outfile = auto_outfile(args.outfile, args.mode, xcap_val)
        out_png = os.path.join(args.outdir, outfile)

        max_abs, _ = plot_diff(
            (label_p, Ns_p, A_p),
            (label_r, Ns_r, A_r),
            out_png,
            xcap_val,
            annotate=annotate,
            stamp_loc=stamp_loc,
        )

        print("DONE")
        print("PLOT:", out_png)
        print("MODE:", args.mode)
        if xcap_val is not None:
            print("XCAP:", xcap_val)
        print("PAIR_BASE:", _pair_base_from_labels(label_p, label_r))
        print("MAX_ABS_DIFF:", max_abs)
        return 0

    series_out: List[Tuple[str, List[int], List[int]]] = []
    for label, Ns_use, Ys_use, meta in raw_series:
        alpha_final = int(meta.get("alpha_final", 0)) if isinstance(meta.get("alpha_final", 0), int) else meta.get("alpha_final", 0)
        series_out.append((f"{label} (alpha_final={alpha_final})", Ns_use, Ys_use))

    if collapse_identical and len(series_out) >= 2:
        if is_primary_replay_pair(series_out[0][0], series_out[1][0]):
            a0 = series_out[0][2]
            a1 = series_out[1][2]
            if len(a0) == len(a1) and all(x == y for x, y in zip(a0, a1)):
                label0, Ns0, Ys0 = series_out[0]
                label_short = label0.replace(" (alpha_final=", "(replay_identical) (alpha_final=")
                series_out = [(label_short, Ns0, Ys0)]

    safe_mkdir(args.outdir)
    outfile = auto_outfile(args.outfile, args.mode, xcap_val)
    out_png = os.path.join(args.outdir, outfile)

    stamp_lines = [
        "SBM Proof Plot (viz-only)",
        f"mode={args.mode}",
        f"xcap={xcap_val}" if xcap_val is not None else "xcap=",
    ]
    if len(series_out) == 1:
        stamp_lines.append(f"alpha_final={series_out[0][0].split('alpha_final=')[-1].rstrip(')')}")
    stamp_text = "\n".join(stamp_lines)

    if args.mode == "delta":
        plot_delta(
            series_out,
            out_png,
            legend_loc=legend_loc,
            annotate=annotate,
            stamp_text=stamp_text,
            stamp_loc=stamp_loc,
        )
    else:
        plot_series_line_step_emergence(
            series_out,
            out_png,
            title=args.title,
            mode=args.mode,
            legend_loc=legend_loc,
            annotate=annotate,
            stamp_text=stamp_text,
            stamp_loc=stamp_loc,
        )

    print("DONE")
    print("PLOT:", out_png)
    print("MODE:", args.mode)
    if xcap_val is not None:
        print("XCAP:", xcap_val)
    print("SERIES:")
    for label, _, _ in series_out:
        print(" -", label)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())