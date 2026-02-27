import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


PHASEC_REQUIRED_FILES = [
    "sbm_ai_results.csv",
    "sbm_ai_alphabet.csv",
    "sbm_ai_metrics.csv",
    "sbm_ai_profile.json",
    "sbm_ai_manifest.sha256",
]

PHASEC_REQUIRED_MANIFEST_ENTRIES = [
    "sbm_ai_results.csv",
    "sbm_ai_alphabet.csv",
    "sbm_ai_metrics.csv",
    "sbm_ai_profile.json",
]

HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass
class BundleResult:
    folder: Path
    ok: bool
    missing_files: List[str]
    manifest_ok: bool
    manifest_errors: List[str]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest_lines(manifest_text: str) -> List[Tuple[str, str]]:
    entries: List[Tuple[str, str]] = []
    for raw in manifest_text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if "=" in line:
            left, right = line.split("=", 1)
            left = left.strip()
            right = right.strip()
            m = re.search(r"\b([0-9a-fA-F]{64})\b", right)
            if not m:
                continue
            digest = m.group(1).lower()
            name = left
            name = re.sub(r"^SHA256\s*\(|^SHA-256\s*\(", "", name, flags=re.IGNORECASE)
            name = re.sub(r"\)\s*$", "", name)
            name = name.strip()
            if name:
                entries.append((name, digest))
            continue

        parts = line.split()
        if len(parts) >= 2 and HEX64_RE.match(parts[0]):
            digest = parts[0].lower()
            name = " ".join(parts[1:]).strip()
            name = name.lstrip("*")
            entries.append((name, digest))
            continue

        m = re.search(r"\b([0-9a-fA-F]{64})\b", line)
        if m:
            digest = m.group(1).lower()
            rest = (line[: m.start()] + line[m.end() :]).strip()
            rest = rest.strip(" -\t")
            if rest:
                entries.append((rest, digest))
            continue

    return entries


def verify_phasec_bundle(folder: Path) -> BundleResult:
    missing: List[str] = []
    manifest_errors: List[str] = []

    for fn in PHASEC_REQUIRED_FILES:
        if not (folder / fn).is_file():
            missing.append(fn)

    if missing:
        return BundleResult(folder=folder, ok=False, missing_files=missing, manifest_ok=False, manifest_errors=["missing_required_files"])

    manifest_path = folder / "sbm_ai_manifest.sha256"
    try:
        manifest_text = manifest_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return BundleResult(folder=folder, ok=False, missing_files=[], manifest_ok=False, manifest_errors=[f"manifest_read_error: {e}"])

    entries = parse_manifest_lines(manifest_text)
    if not entries:
        return BundleResult(folder=folder, ok=False, missing_files=[], manifest_ok=False, manifest_errors=["manifest_parse_failed_or_empty"])

    seen = set()
    for name, digest in entries:
        seen.add(name)
        file_path = folder / name
        if not file_path.is_file():
            manifest_errors.append(f"manifest_lists_missing_file: {name}")
            continue
        try:
            actual = sha256_file(file_path)
        except Exception as e:
            manifest_errors.append(f"hash_read_error: {name}: {e}")
            continue
        if actual.lower() != digest.lower():
            manifest_errors.append(f"hash_mismatch: {name}: manifest={digest.lower()} actual={actual.lower()}")

    for fn in PHASEC_REQUIRED_MANIFEST_ENTRIES:
        if fn not in seen:
            manifest_errors.append(f"manifest_missing_required_entry: {fn}")

    manifest_ok = (len(manifest_errors) == 0)
    ok = manifest_ok

    return BundleResult(folder=folder, ok=ok, missing_files=[], manifest_ok=manifest_ok, manifest_errors=manifest_errors)


def read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def compare_manifests(primary: Path, replay: Path) -> Tuple[bool, str]:
    p = primary / "sbm_ai_manifest.sha256"
    r = replay / "sbm_ai_manifest.sha256"
    if not p.is_file() or not r.is_file():
        return (False, "missing_manifest_in_primary_or_replay")
    if read_bytes(p) == read_bytes(r):
        return (True, "manifest_byte_identical")
    return (False, "manifest_not_identical")


def parse_operator_registry(registry_path: Path) -> List[Dict[str, str]]:
    if not registry_path.is_file():
        return []
    text = registry_path.read_text(encoding="utf-8", errors="replace").splitlines()

    blocks: List[List[str]] = []
    cur: List[str] = []
    for line in text:
        if line.strip() == "":
            if cur:
                blocks.append(cur)
                cur = []
            continue
        if line.strip().startswith("SBM OPERATOR REGISTRY"):
            continue
        cur.append(line.rstrip())
    if cur:
        blocks.append(cur)

    ops: List[Dict[str, str]] = []
    for b in blocks:
        d: Dict[str, str] = {}
        d["operator"] = b[0].strip()
        for line in b[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                d[k.strip().lower()] = v.strip()
        ops.append(d)
    return ops


def fmt_bundle(res: BundleResult) -> str:
    out: List[str] = []
    out.append(f"FOLDER: {str(res.folder)}")
    out.append(f"STATUS: {'PASS' if res.ok else 'FAIL'}")
    out.append(f"MANIFEST_STATUS: {'PASS' if res.manifest_ok else 'FAIL'}")
    if res.missing_files:
        out.append("MISSING_FILES:")
        for m in res.missing_files:
            out.append(f"  {m}")
    if res.manifest_errors:
        out.append("MANIFEST_ERRORS:")
        for e in res.manifest_errors:
            out.append(f"  {e}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs", default="outputs")
    ap.add_argument("--use_registry", action="store_true")
    ap.add_argument("--phasec_only", action="store_true")
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    outputs_dir = Path(args.outputs).resolve()
    if not outputs_dir.is_dir():
        print(f"FAIL: outputs_dir_not_found: {outputs_dir}")
        return 2

    registry_path = outputs_dir / "OPERATOR_REGISTRY_PHASEC.txt"
    if not registry_path.is_file():
       registry_path = outputs_dir / "OPERATOR_REGISTRY.txt"
    ops = parse_operator_registry(registry_path) if args.use_registry else []

    lines: List[str] = []
    lines.append("SBM CONFORMANCE VERIFIER")
    lines.append("MODE: registry" if ops else "MODE: phasec_autodiscovery")
    if args.use_registry:
        lines.append(f"REGISTRY: {str(registry_path)}")
        lines.append(f"PHASEC_ONLY: {'YES' if args.phasec_only else 'NO'}")
    lines.append("")

    overall_ok = True

    if ops:
        for op in ops:
            op_name = op.get("operator", "UNKNOWN")
            primary_rel = op.get("primary_folder", "")
            replay_rel = op.get("replay_folder", "")

            if args.phasec_only and "AI_FRACTURE" not in op_name:
                continue

            lines.append(f"OPERATOR: {op_name}")

            primary = (outputs_dir.parent / primary_rel).resolve() if primary_rel else None
            replay = (outputs_dir.parent / replay_rel).resolve() if replay_rel else None

            if primary is None or not primary.is_dir():
                lines.append("PRIMARY_BUNDLE: FAIL (missing_or_invalid_primary_folder)")
                overall_ok = False
            else:
                res_p = verify_phasec_bundle(primary)
                lines.append("PRIMARY_BUNDLE:")
                lines.append(fmt_bundle(res_p))
                if not res_p.ok:
                    overall_ok = False

            if replay_rel:
                if replay is None or not replay.is_dir():
                    lines.append("REPLAY_BUNDLE: FAIL (missing_or_invalid_replay_folder)")
                    overall_ok = False
                else:
                    res_r = verify_phasec_bundle(replay)
                    lines.append("REPLAY_BUNDLE:")
                    lines.append(fmt_bundle(res_r))
                    if not res_r.ok:
                        overall_ok = False

                if primary is not None and replay is not None and primary.is_dir() and replay.is_dir():
                    ok_m, msg = compare_manifests(primary, replay)
                    lines.append(f"PRIMARY_VS_REPLAY_MANIFEST: {'PASS' if ok_m else 'FAIL'} ({msg})")
                    if not ok_m:
                        overall_ok = False

            lines.append("")

    else:
        for child in sorted(outputs_dir.iterdir()):
            if not child.is_dir():
                continue
            if not (child / "sbm_ai_manifest.sha256").is_file():
                continue
            res = verify_phasec_bundle(child)
            lines.append(fmt_bundle(res))
            lines.append("")
            if not res.ok:
                overall_ok = False

    lines.append(f"OVERALL_STATUS: {'PASS' if overall_ok else 'FAIL'}")

    report_text = "\n".join(lines)
    print(report_text)

    if args.report:
        try:
            Path(args.report).parent.mkdir(parents=True, exist_ok=True)
            Path(args.report).write_text(report_text, encoding="utf-8")
        except Exception as e:
            print(f"REPORT_WRITE_FAIL: {e}")
            return 3

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())