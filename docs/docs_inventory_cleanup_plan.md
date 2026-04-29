# Docs Inventory Cleanup Plan

This plan classifies every markdown file that was present in `docs/` before cleanup. The goal is to keep the active docs folder focused on the current registry-centered workflow, the current pilot result, and the next-step operating plan.

| filename | classification | short reason | action |
| --- | --- | --- | --- |
| `dataset_feasibility_audit.md` | archive_reference | Phase 0 audit trail for an earlier stage; useful history, not active workflow. | Move to `archive/docs_reference/` |
| `example_ingestion_and_registry_sop.md` | keep_active | Main operational workflow doc for future work. | Keep in `docs/` |
| `examples_registry_schema.md` | keep_active | Defines the canonical registry schema and active build path. | Keep in `docs/` |
| `forward_pass_pilot.md` | archive_reference | Detailed runtime summary for a completed pilot stage on example 369. | Move to `archive/docs_reference/` |
| `head_ablation_pilot.md` | archive_reference | Historical pilot-stage result detail; useful for audit, not active workflow. | Move to `archive/docs_reference/` |
| `head_patching_pilot.md` | archive_reference | Historical pilot-stage result detail; useful for audit, not active workflow. | Move to `archive/docs_reference/` |
| `implementation_bootstrap.md` | archive_reference | Early implementation map; useful context, but no longer central to day-to-day workflow. | Move to `archive/docs_reference/` |
| `layer_patching_pilot.md` | archive_reference | Historical pilot-stage result detail; useful for audit, not active workflow. | Move to `archive/docs_reference/` |
| `next_candidate_triage.md` | archive_reference | One-off shortlist document tied to an archived intermediate candidate pass. | Move to `archive/docs_reference/` |
| `next_example_plan.md` | keep_active | Still relevant as the current forward plan for adding one more validated example. | Keep in `docs/` |
| `next_round_batch_5.md` | archive_reference | Batch-selection checkpoint for an intermediate narrowing step; not part of the active workflow now. | Move to `archive/docs_reference/` |
| `next_round_review_top3.md` | archive_reference | Top-3 narrowing checkpoint now reflected in the active review sheet and registry. | Move to `archive/docs_reference/` |
| `next_round_token_span_feasibility.md` | archive_reference | Useful history for why 2265/2781 were parked and why 813/3573/2793 advanced. | Move to `archive/docs_reference/` |
| `pair_construction_pilot.md` | archive_reference | Earlier pair-authoring stage notes; still useful as historical context, but not active workflow. | Move to `archive/docs_reference/` |
| `pair_validation_run1.md` | archive_reference | Historical validation run detail for 51 and 369; retained as audit trail. | Move to `archive/docs_reference/` |
| `pilot_mechanistic_findings_369.md` | keep_active | Best compact summary of the current validated pilot mechanistic result. | Keep in `docs/` |
| `prd_operational_addendum.md` | keep_active | Current policy-level addendum for dataset roles and registry use. | Keep in `docs/` |
| `ragtruth_leads_policy.md` | keep_active | Current policy doc for auxiliary RAGTruth leads. | Keep in `docs/` |
| `token_span_feasibility.md` | archive_reference | Historical first-batch token-mapping record; useful audit context, not active workflow. | Move to `archive/docs_reference/` |
| `tracing_pilot_prep.md` | archive_reference | Intermediate tracing-prep checkpoint for the completed 369 pilot. | Move to `archive/docs_reference/` |
| `validated_pair_summary.md` | archive_reference | Historical validation checkpoint now largely superseded by the pilot findings summary. | Move to `archive/docs_reference/` |
| `workspace_audit.md` | archive_reference | Initial workspace/orientation document; not needed for current operations, but worth retaining as setup history. | Move to `archive/docs_reference/` |

## Summary
- `keep_active`: 6 files
- `archive_reference`: 16 files
- `safe_to_delete`: 0 files

## Notes
- I chose archive over delete whenever a document still provided reproducibility, audit trail, or setup context.
- No markdown files were classified as `safe_to_delete`; none looked like an empty placeholder or fully redundant zero-value artifact.
- After cleanup, the active docs folder should be centered on the registry workflow, policy/SOP, the current pilot result, and the next-step plan.
