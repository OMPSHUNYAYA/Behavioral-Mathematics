SBM PHASE C RELEASE CAPSULE

Purpose:
This capsule contains a deterministic, replay-verified Phase C operator bundle and the verifier capsule required to reproduce conformance.

Contents:
release_phasec\outputs\ai_fracture
release_phasec\outputs\ai_fracture_replay
release_phasec\outputs\OPERATOR_REGISTRY_PHASEC.txt
release_phasec\verify\verify_sbm.py
release_phasec\verify\RUN_ALL_VERIFY.cmd

How to verify:
From inside release_phasec:
verify\RUN_ALL_VERIFY.cmd

Expected:
OVERALL_STATUS: PASS
EXIT_CODE: 0

Determinism guarantee:
Primary and replay manifests are byte-identical and artifact hashes match the manifest.

Integrity demonstration:
Tamper ritual proof is included in:
verify\TAMPER_RITUAL_PROOF.txt