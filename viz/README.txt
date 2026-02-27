SBM Visualization Layer (Non-Frozen)

This folder is intentionally excluded from the SBM deterministic freeze boundary.

Purpose:
- Produce human-readable plots from deterministic evidence artifacts
- Improve interpretability and presentation
- Preserve deterministic core integrity

Conformance:
- SBM conformance is defined only by exact replay identity: `B_A = B_B`
- Visualization outputs are NOT part of conformance
- Visualization is optional and may evolve independently

Data Source Rule:
- Visualization scripts must read only from deterministic artifacts (e.g., `reference_outputs/`)
- Visualization scripts must not modify any frozen folder or artifact

Generated proof plots (if present) may be hash-recorded in viz/out/VIZ_MANIFEST.sha256.txt for audit traceability.