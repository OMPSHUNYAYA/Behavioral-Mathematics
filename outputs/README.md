# ⭐ outputs/

**This folder is intentionally empty in the public repository.**

It serves as the **runtime artifact directory** for SBM executions.

Artifacts generated here are **ephemeral runtime artifacts** and are **not authoritative conformance evidence**.

---

# **Purpose**

When executing:

`python scripts\sbm_test.py --op xorshift_parity --N 3000000 --H 19 --out outputs\run1`

or

`python scripts\sbm_test.py --op xorshift_parity --N 3000000 --H 19 --out outputs\run2`

Parameters shown above are illustrative and may differ from the canonical verification profile.

SBM will generate deterministic artifact bundles inside this folder.

These artifacts demonstrate runtime enforcement of:

- **Deterministic structural state computation** `X(t) = (m(t), a(t), s(t))`
- **Bounded-horizon window discipline** `W_H(t)`
- **Deterministic structural alphabet transitions**
- **Conservative collapse invariant** `phi((m,a,s)) = m`
- **Replay identity requirement** `B_A = B_B`

---

# **What This Folder Contains**

This folder may contain:

- `sbm_results.csv`
- `sbm_alphabet.csv`
- `sbm_metrics.csv`
- `sbm_profile.json`
- `sbm_manifest.sha256`

Optional temporary files may also appear during execution.

These files:

- **May be deleted safely**
- **May be regenerated at any time**
- **Are not sealed**
- **Are not authoritative**

---

# **What This Folder Is NOT**

This folder is **not**:

- The canonical conformance evidence bundle  
- The replay-verified reference set  
- The fingerprint-locked certification boundary  
- The authoritative definition of conformance  

Authoritative replay-verified artifacts are stored under:

`reference_outputs/`

Deterministic freeze-boundary certification is enforced by:

`scripts/`  
`verify/`  
`reference_outputs/`  
`release_phasec/`

---

# **Reproducibility (Manual Replay Demonstration)**

To demonstrate deterministic replay identity:

`python scripts\sbm_test.py --op xorshift_parity --N 3000000 --H 19 --out outputs\run1`

`python scripts\sbm_test.py --op xorshift_parity --N 3000000 --H 19 --out outputs\run2`

Then compare manifests:

**Windows**

`fc /b outputs\run1\sbm_manifest.sha256 outputs\run2\sbm_manifest.sha256`

Expected result:

`FC: no differences encountered`

This demonstrates:

**Replay identity condition:** `B_A = B_B`

Byte identity is mandatory.

There is:

- **No tolerance layer**
- **No approximate equality**
- **No probabilistic arbitration**

---

# **Why This Separation Exists**

This strict separation preserves:

- **Deterministic execution discipline**
- **Clear boundary between runtime artifacts and frozen conformance evidence**
- **Replay-verifiable governance**
- **Conservative magnitude preservation**
- **Structural alphabet integrity**

Structural roles:

`outputs/` → execution artifacts  
`reference_outputs/` → frozen proof artifacts  
`verify/` → replay enforcement  

---

# **Conformance Authority**

SBM conformance is defined strictly by:

`B_A = B_B`

Runtime artifacts are reproducible.  
Proof artifacts are frozen.
