# Example Ingestion And Registry SOP

This is the main operational workflow for future students. The registry is canonical for admitted examples only.

## 1. Direct Exploration Path From RAGTruth_Xtended
1. Start from RAGTruth_Xtended for primary candidate exploration.
2. Identify promising short-span candidates using the existing triage guidance.
3. Record exploratory outputs in temporary triage artifacts, not directly in the canonical registry unless the example is being admitted.

## 2. RAGTruth Reproduced Lead Path
1. Store reproduced leads in a separate sheet such as `data/ragtruth_reproduced_leads.csv`.
2. Treat each lead as auxiliary only until it has been checked against the project criteria.
3. Prefer response-level matching over weak source-only matching.

## 3. Pre-Registry Checks
1. Confirm the lead or direct candidate corresponds to a concrete RAGTruth_Xtended example or other accepted substrate row.
2. Confirm the hallucinated behaviour is scientifically relevant to the current project scope.
3. Reject leads that are weakly matched, diffuse, approximation-heavy, or otherwise unsuitable before registry admission.
4. If the lead is strong and matched confidently, preserve provenance metadata such as temperature when available.

## 4. Registry Admission Rule
1. Admit an example to `outputs/examples_registry.csv` only after it has passed pre-registry checks.
2. For direct RAGTruth_Xtended exploration, the admitted row should carry `candidate_source=direct_xtended`.
3. For an admitted auxiliary lead, the row should carry `candidate_source=ragtruth_reproduced_lead` and the relevant lead provenance fields.
4. Non-admitted leads stay outside the registry.

## 5. Token Mapping
1. Run token-span feasibility on admitted examples.
2. Set `token_mapping_status` to `clean`, `ambiguous`, `failed`, or `needs_checking`.
3. Park ambiguous or failed rows unless there is an explicit split-token plan.

## 6. Human Review
1. Work directly in the registry for admitted examples.
2. Fill `ground_truth_text_verified`, `corrupted_prompt_candidate`, `edit_class`, `edit_delta_text`, and `why_minimal`.
3. Leave rows parked if the corrective edit is not minimal or the truth target is not crisp enough.

## 7. Pair Validation
1. Filter the registry by `validation_target_flag=true`.
2. Run only the current approved model scope.
3. Update `clean_reproduction_status`, `corrupted_flip_status`, `validated_pair_flag`, `validation_notes`, and `validation_results_path`.
4. Reject or park rows that do not pass the validation gate.

## 8. Tracing Lifecycle
1. Promote only validated pairs into tracing by setting `tracing_target_flag=true`.
2. Run tracing stages in order: tracing prep, forward pass, layer patching, head patching, and any approved ablation stage.
3. Update `tracing_status`, tracing artifact fields, and `last_updated_stage` as the example advances.

## 9. Final Statuses
- Use `final_status=ready_for_validation` for authored rows selected for validation.
- Use `final_status=parked` for deferred but still potentially useful rows.
- Use `final_status=processed_reject` for rows that failed and should not be reused casually.
- Use `final_status=pilot_complete` for completed pilot examples such as `369`.

## 10. Builder Usage
1. Rebuild the registry from the current active working inputs:
   ```bash
   python3 scripts/build_examples_registry.py
   ```
   Default active inputs:
   - `outputs/pair_authoring_review_sheet.csv`
   - `outputs/next_round_review_sheet_top3.csv`
   Older intermediate CSVs live under `archive/legacy_csvs/` and are not part of the active default build path.
2. To merge an auxiliary lead sheet without auto-admitting unmatched leads:
   ```bash
   python3 scripts/build_examples_registry.py --input data/ragtruth_reproduced_leads.csv
   ```
3. Only if a lead sheet already contains explicitly admitted rows with valid `example_id` values and you intend those rows to create new registry entries, use:
   ```bash
   python3 scripts/build_examples_registry.py --input data/ragtruth_reproduced_leads.csv --allow-new-lead-rows
   ```
4. Warning: Use `--allow-new-lead-rows` only after a lead has already passed pre-registry checks and has been manually approved for registry admission.
