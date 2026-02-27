# ⭐ Shunyaya Behavioral Mathematics (SBM)

**Deterministic Structural Behavioral Mathematics — Without Modifying Classical Systems**

![SBM](https://img.shields.io/badge/SBM-Structural%20Behavioral%20Mathematics-blue)
![Deterministic](https://img.shields.io/badge/Deterministic-Replay--Verified-green)
![Invariant](https://img.shields.io/badge/Invariant-phi%28%28m%2Ca%2Cs%29%29%20%3D%20m-green)
![Replay](https://img.shields.io/badge/Replay%20Identity-B_A%20%3D%20B_B-green)
![Standard](https://img.shields.io/badge/Standard-Open-blue)
![Verification](https://img.shields.io/badge/Verification-Civilization--Grade-purple)

**Replay-Verified • Conservative Magnitude Preservation • Bounded Horizon • Open Standard**

---

# 🔒 Conformance Contract

SBM conformance is defined solely by exact replay identity:

`B_A = B_B`

Collapse invariant (non-negotiable):

`phi((m,a,s)) = m`

Where:

- `m` = classical magnitude  
- `a` = structural alignment  
- `s` = accumulated structural posture  

Magnitude remains untouched.

There is:

- No randomness  
- No tolerance  
- No approximate equality  
- No probabilistic equivalence  
- No adaptive mutation  
- No statistical acceptance  

If any verification phase fails, SBM conformance fails.

Conformance is binary and determined exclusively by replay identity.

---

## 🔗 Quick Links

### 📘 Documentation

- [Quickstart Guide](docs/Quickstart.md)  
- [FAQ](docs/FAQ.md)  
- [SBM Structural Behavioral Model](docs/SBM-Structural-Behavioral-Model.md)  
- [SBM Conformance Specification](docs/SBM-Conformance-Specification.md)  
- [SBM Structural Topology Diagram](docs/SBM-Topology-Diagram.png)  
- [Full Specification (PDF)](docs/SBM_v1.8.pdf)  
- [Concept Flyer (High-Level Overview PDF)](docs/Concept-Flyer_SBM_v1.8.pdf)

Documentation directory:

- [`docs/`](docs/)

---

### ⚙ Deterministic Verification (Canonical Entrypoint)

Primary verification orchestrator:

- [`verify/RUN_VERIFY_ALL_PHASES.cmd`](verify/RUN_VERIFY_ALL_PHASES.cmd)

Verification directory:

- [`verify/`](verify/)

Run (official multi-phase verification):

`verify\RUN_VERIFY_ALL_PHASES.cmd`

Expected result:

`PHASE_A_STATUS: PASS`  
`PHASE_B_STATUS: PASS`  
`PHASE_C_STATUS: PASS`  
`OVERALL_STATUS: PASS`  
`EXIT_CODE: 0`

Conformance authority condition:

`B_A = B_B`

Byte identity is required.  
No tolerance.  
No probabilistic equivalence.

Core invariant preserved:

`phi((m,a,s)) = m`

---

### 🧪 Deterministic Operator Execution

Primary deterministic operator:

- [`scripts/sbm_test.py`](scripts/sbm_test.py)

Scripts directory:

- [`scripts/`](scripts/)

Example replay verification:

Primary run:

```
python scripts\sbm_test.py --op xorshift_parity --N 3000000 --H 19 --out OUT_PRIMARY
```

Replay run:

```
python scripts\sbm_test.py --op xorshift_parity --N 3000000 --H 19 --out OUT_REPLAY
```

Replay succeeds only if:

`B_A = B_B`

Compare manifests:

```
fc /b OUT_PRIMARY\sbm_manifest.sha256 OUT_REPLAY\sbm_manifest.sha256
```

Replay identity is authoritative proof.

---

### 📂 Replay Evidence Structure

Runtime outputs (generated locally, not part of freeze boundary):

- [`outputs/`](outputs/)  
- [`outputs/README.md`](outputs/README.md)

These are ephemeral and regenerated locally.

Authoritative replay reference anchors:

- [`reference_outputs/`](reference_outputs/)  
- [`reference_outputs/phase_a/`](reference_outputs/phase_a/)  
- [`reference_outputs/phase_b/`](reference_outputs/phase_b/)  

These provide deterministic replay anchors and structural fingerprints.

Capsule-level structural freeze verification boundary:

- [`release_phasec/`](release_phasec/)

This enforces frozen operator registry validation and capsule replay discipline.

Conformance is defined strictly by deterministic replay identity — not by static artifact hosting.

---

### 📊 Visualization Layer (Optional, Non-Conformance)

Visualization utilities:

- [`viz/`](viz/)  
- [`viz/plot_alpha_curve.py`](viz/plot_alpha_curve.py)  
- [`viz/README.txt`](viz/README.txt)
- [`viz/out/`](viz/out/)

Example:

`python viz\plot_alpha_curve.py --mode diff --xcap 500`

Visualization reads frozen artifacts but does not participate in conformance.

Formal conformance remains defined solely by:

`B_A = B_B`

---

### 📜 License

- [`LICENSE`](LICENSE)

Shunyaya Behavioral Mathematics (SBM) is published as an open standard.

Conformance is defined structurally — not institutionally — through exact replay identity:

`B_A = B_B`

---

# 🧾 Evidence Hierarchy (Deterministic Authority Ladder)

SBM verification follows a strict evidence hierarchy. Each level enforces:

`B_A = B_B`

**Level 1 — Local Deterministic Replay**  
Exact replay validation on a single machine.

**Level 2 — Cross-Execution Replay**  
Independent repeated execution under identical declared parameters.

**Level 3 — Phase A Validation**  
Deterministic replay identity on controlled structural operator.

**Level 4 — Phase B Validation**  
Large-scale multi-million sample replay identity validation.

**Level 5 — Phase C Validation**  
Capsule-level operator registry verification and structural fracture classification.

**Level 6 — Frozen Boundary Capsule Verification**  
Independent artifact replay validation under structural freeze discipline.

At every level, conformance authority remains:

`B_A = B_B`

No narrative, visualization, or interpretation overrides artifact identity.

---

# ✅ 60-Second Verification (Start Here)

SBM is verified by deterministic replay — not interpretation.

Verification succeeds if and only if:

`B_A = B_B`

Artifacts must be byte-identical.

If not byte-identical, the run is NOT VERIFIED.

---

# 🔐 Fastest Verification Method (Official Multi-Phase Orchestrator)

From project root:

`verify\RUN_VERIFY_ALL_PHASES.cmd`

Expected terminal output:

`PHASE_A_STATUS: PASS`  
`PHASE_B_STATUS: PASS`  
`PHASE_C_STATUS: PASS`  
`OVERALL_STATUS: PASS`  
`EXIT_CODE: 0`

If replay identity fails, SBM fails.

There is no partial success.

---

# 🔁 Manual Deterministic Replay (Illustrative)

Primary run:

`python scripts\sbm_test.py --op xorshift_parity --N 3000000 --H 19 --out OUT_PRIMARY`

Replay run:

`python scripts\sbm_test.py --op xorshift_parity --N 3000000 --H 19 --out OUT_REPLAY`

Conformance condition:

`B_A = B_B`

---

# 🧭 What SBM Is

Shunyaya Behavioral Mathematics (SBM) is a deterministic structural overlay that evaluates ordered system evolution without altering classical magnitude.

Core invariant:

`phi((m,a,s)) = m`

Magnitude remains primary.  
Structural posture becomes observable.

---

# 🧮 Core State Model

Each observation is represented as:

`X(t) = (m(t), a(t), s(t))`

Where:

- `m(t)` = classical magnitude  
- `a(t)` = structural alignment  
- `s(t)` = accumulated structural posture  

Signature extraction operates under fixed deterministic horizon `H`.

---

# 🧱 Bounded Horizon Discipline

SBM evaluates structural behavior within fixed deterministic horizon:

`W_H(t) = {t-H+1, ..., t}`

---

# 🔤 Structural Alphabet Discipline

SBM generates a finite structural alphabet:

`Sigma = {sigma_0, ..., sigma_L}`

Alphabet is finite, deterministic, and replay-stable.

---

# 📊 Core Structural Invariants

Structural reporting uses deterministic invariants:

`alpha(N,H)` = number of distinct signatures  
`gamma(H,N)` = log2(alpha(N,H)) / H  
`R_alpha(H,N)` = alpha(N,H) / 2^H  
`R_cf(H,N)` = last emergence / 2^H  
`E_N` = emergence_count / N  

---

# 🛡 Deterministic Conformance Conditions

Conformance requires:

- `phi((m,a,s)) = m` preserved  
- Fixed horizon `H`  
- Finite alphabet  
- Deterministic transitions  
- Replay identity `B_A = B_B`

---

# 🧠 Why SBM Exists

Classical mathematics evaluates magnitude correctness.

SBM evaluates structural posture evolution while preserving magnitude.

---

# 🌍 Open Standard

SBM is published as an **Open Standard** under an open license.

This project is provided **as-is, without warranty**.

Attribution is recommended but not required:

"Implements Shunyaya Behavioral Mathematics (SBM)"

Conformance defined exclusively by:

`B_A = B_B`

---

# One-Line Summary

**Shunyaya Behavioral Mathematics (SBM)** introduces deterministic structural alphabet discipline, preserves magnitude via `phi((m,a,s)) = m`, and defines conformance strictly through replay identity `B_A = B_B`.
