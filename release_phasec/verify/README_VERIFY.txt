SBM VERIFY CAPSULE

This folder contains the conformance verifier for SBM Phase C deterministic bundles.

Preferred registry:
outputs\OPERATOR_REGISTRY_PHASEC.txt

Fallback registry:
outputs\OPERATOR_REGISTRY.txt

Run command:
python verify\verify_sbm.py --outputs outputs --use_registry --report verify\last_verify_report.txt

Expected result:
OVERALL_STATUS: PASS

Verifier guarantees:

Required Phase C artifacts exist.

SHA-256 recomputation matches manifest entries.

Primary and replay manifests are byte-identical.