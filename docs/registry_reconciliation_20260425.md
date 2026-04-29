# Registry Reconciliation 2026-04-25

## Reason
The local `outputs/examples_registry.csv` was stale because Colab-side registry updates were not copied back before the runtime was lost. No experiments were rerun for this reconciliation.

## Backup
- Backup created before edits: `outputs/examples_registry.backup_before_reconcile.csv`

## Rows Updated
- `813`
- `3573`

No other registry rows were intentionally changed.

## Evidence Used
- Pair validation for `813`: `outputs/runs/20260425_060337_pair_validation_813/`
- Pair validation mixed batch for `3573`: `outputs/runs/20260425_050240_pair_validation_813_3573/`
- Forward pass for `813`: `outputs/runs/20260425_064458_forward_pass_813/`
- Layer patching for `813`: `outputs/runs/20260425_070723_layer_patching_813/`
- Head patching for `813`: `outputs/runs/20260425_073014_head_patching_813/`
- Head ablation for `813`: `outputs/runs/20260425_075129_head_ablation_813/`

## Final Decisions
- `813` was reconciled to `final_status=pilot_complete` and `tracing_status=pilot_complete` because it completed pair validation, forward pass, layer patching, head patching, and head ablation.
- `813` latest run pointers now point to `outputs/runs/20260425_075129_head_ablation_813`.
- `3573` was reconciled to `final_status=processed_reject` because pair validation failed: the clean run did not reproduce the target hallucination and the corrupted run did not flip to the verified truth.
- `3573` was removed from the validation target queue with `validation_target_flag=FALSE`.

## Notes
- The local saved pair-validation result file for `813` is `outputs/runs/20260425_060337_pair_validation_813/pair_validation_results_813.jsonl`, so the registry points to that concrete artifact.
- This reconciliation only updates concise registry state. Raw run outputs remain in the run folders.
