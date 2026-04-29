# Examples Registry Schema

`outputs/examples_registry.csv` is the canonical per-example working registry for admitted and managed examples across the project lifecycle. Future scripts should read from this file and filter rows by status/control columns instead of introducing new ad hoc CSV sheets.

RAGTruth reproduced leads are allowed as an auxiliary upstream lead source, but they do not enter the registry automatically. They must first pass pre-registry checks and be explicitly admitted as accepted examples.

## Build Command
```bash
python scripts/build_examples_registry.py
```

By default, the builder preserves live stage-owned state from an existing `outputs/examples_registry.csv` before writing the rebuilt registry. This protects fields written by run-folder scripts, including latest run pointers, token-span status, validation status, validation result paths, final workflow status, keep reasons, and tracing status. Use `--reset` only when you intentionally want to discard live experiment state and rebuild from source sheets plus defaults.

## Source Inputs
Current active default inputs:
- `outputs/pair_authoring_review_sheet.csv`
- `outputs/next_round_review_sheet_top3.csv`
- Optional auxiliary input, when explicitly provided:
  - `data/ragtruth_reproduced_leads.csv`

Older intermediate CSVs and similar stale artifacts are archived under `archive/legacy_csvs/` and are not part of the active default build path.

If a RAGTruth lead sheet is provided to the builder, lead rows augment the canonical registry only after admission. By default, non-admitted lead rows are skipped and remain pre-registry.

## Column Groups

### Core Identity
- `example_id`: stable example key used across all stages.
- `source_id`: upstream dataset source id when available.
- `source_category`: coarse dataset/source bucket such as `CNN/DM`.
- `task_type`: upstream task label such as `Summary`.
- `registry_source_files`: semicolon-separated archive inputs that contributed to the merged row.

### Auxiliary Lead Provenance
- `candidate_source`: origin route for the admitted example. Allowed values:
  - `direct_xtended`
  - `ragtruth_reproduced_lead`
  - `other_auxiliary`
- `lead_match_status`: how strongly an auxiliary lead was matched before or during admission. Allowed values:
  - `not_applicable`
  - `matched_high_confidence`
  - `matched_low_confidence`
  - `unmatched`
  - `rejected_pre_registry`
- `generation_metadata_source`: where auxiliary generation metadata came from. Allowed values:
  - `xtended`
  - `ragtruth`
  - `manual`
  - `unknown`
- `source_generation_temperature`: auxiliary generation temperature if available and trusted enough to preserve as provenance.
- `source_generation_notes`: short notes about any recovered generation settings or caveats.
- `ragtruth_response_id`: upstream RAGTruth response identifier when a lead was matched confidently enough to preserve provenance.
- `ragtruth_source_id`: upstream RAGTruth source/document identifier.
- `ragtruth_model`: RAGTruth model label associated with the reproduced lead.
- `ragtruth_reproduction_verified`: whether manual review confirmed that the RAGTruth lead truly reproduced the target hallucination.
- `ragtruth_new_behaviour_change`: short note on any observed behavioral difference in the reproduced lead.
- `lead_ingestion_notes`: operator notes from pre-registry lead triage and admission.

These fields do not weaken the current gating. They exist to preserve auxiliary provenance once a lead has already passed pre-registry checks and been admitted.

### Static Extracted Fields
- `category`: normalized project category such as `date/year`, `number/count`, or `entity/title`.
- `why_shortlisted`: short triage rationale for why the example looks promising.
- `likely_divergence_type`: coarse expected divergence type, typically `lexical_semantic`.
- `recommended_priority_rank`: manual review priority from triage.
- `minimal_edit_feasible`: triage judgment about whether a minimal corrective edit looks practical.
- `raw_prompt_field`: raw dataset prompt string.
- `raw_source_info_field`: raw dataset source/context string.
- `clean_input_text_for_validation`: clean input used for validation.
- `supporting_context_excerpt`: context/evidence excerpt preserved for review.
- `original_response`: original model response from the dataset row.
- `raw_ground_truth_field`: raw dataset metadata for the labeled target.
- `hallucinated_substring`: labeled hallucinated text span.
- `hallucinated_char_span`: labeled character span.
- `prompt_fallback_warning`: warning field if clean-input fallback logic was required.

### Token Mapping Fields
- `token_mapping_status`: `clean`, `ambiguous`, `failed`, or `needs_checking`.
- `token_mapping_known`: `yes` when a token-span determination is already known.
- `hallucinated_token_span`: token span for the hallucinated substring when known.
- `first_hallucinated_token_index`: first token index for the hallucinated substring when known.
- `token_mapping_notes`: free-form notes about token-boundary issues.

### Human Review Fields
- `ground_truth_text_verified`
- `corrupted_prompt_candidate`
- `edit_class`
- `edit_delta_text`
- `why_minimal`
- `semantic_equivalence_check`
- `reviewer_notes`

These are the manual authoring and review columns that future annotation passes should update in place.

### Validation Fields
- `validation_target_flag`: `true` if the example is queued for the next validation run.
- `clean_reproduction_status`
- `corrupted_flip_status`
- `validated_pair_flag`: `true` if the example has passed the clean/corrupted validation gate.
- `validation_notes`: short status note for the last validation decision.
- `validation_results_path`: path to the run artifact that established the current validation state.

### Tracing Fields
- `tracing_target_flag`: `true` if the example is selected for tracing.
- `tracing_status`: coarse tracing stage state such as `not_started`, `parked`, or `pilot_complete`.
- `built_clean_prompt`
- `built_corrupted_prompt`
- `tracing_notes`

These fields reserve a stable place for prompt artifacts and tracing state without requiring another schema change later.

### Workflow Control Fields
- `triage_status`: triage-level decision such as `shortlisted`, `processed_keep`, or `processed_reject`.
- `pair_authoring_status`: `not_started`, `in_progress`, or `authored`.
- `final_status`: current top-level state such as `ready_for_validation`, `parked`, `processed_reject`, or `pilot_complete`.
- `keep_reason`: concise explanation for why the example is kept, parked, or rejected.
- `last_updated_stage`: last project stage that materially changed the example row.
- `latest_run_id`: latest run-folder ID that updated the row.
- `latest_artifact_root`: latest `outputs/runs/<run_id>/` folder that updated the row.
- `latest_stage_status`: concise status from the latest stage update, such as `success` or `failed`.
- `latest_stage_notes`: short operational note from the latest stage update.

Run-tracking fields are summaries only. Full per-run records belong under `outputs/runs/<run_id>/`.

## Lifecycle Relationship
1. Direct RAGTruth_Xtended exploration remains the default path for finding candidates.
2. RAGTruth reproduced leads may be stored in a separate lead sheet and reviewed as auxiliary evidence.
3. Pre-registry checks decide whether a lead is confidently matched, scientifically relevant, and eligible for admission.
4. Only accepted examples belong in `outputs/examples_registry.csv`.
5. Once admitted, any trustworthy RAGTruth generation metadata may be copied into the auxiliary lead-provenance fields without changing the tracing substrate, which remains RAGTruth_Xtended.

## Filtering Guidance
- Triage candidates: filter `triage_status` and `recommended_priority_rank`.
- Token-span work: filter `token_mapping_status`.
- Pair authoring: filter `pair_authoring_status`.
- Validation runs: filter `validation_target_flag == true`.
- Validated tracing inputs: filter `validated_pair_flag == true` and `tracing_target_flag == true`.
- Completed pilot evidence: filter `final_status == pilot_complete`.
- Auxiliary provenance review: inspect `candidate_source`, `lead_match_status`, and `generation_metadata_source`.
- Latest artifacts: inspect `latest_artifact_root` first, then open that run's `manifest.json` and `summary.json`.
