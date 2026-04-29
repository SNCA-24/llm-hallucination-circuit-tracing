# Pair Construction Pilot & Truth Recovery

## Overview
This document prepares the 4 strictly selected examples (51, 369, 597, 93) for human-in-the-loop manual truth recovery and pair authoring.
These examples were retained based on flawless character->token spans. We are explicitly decoupling truth-extraction from prompt-formatting to remain conservative.

## Important Semantic Field Changes
- **Prompt vs Context**: We previously used a collapsed `original_prompt` field. We have corrected this semantic export bug.
- **Clean Prompt**: The field `clean_input_text_for_validation` is mapped directly from the dataset's raw `prompt` field. This is the actual instruction passed to the LLM.
- **Context/Evidence**: The field `supporting_context_excerpt` is strictly sourced from `source_info`, which houses the document base.
- **Fallback Policy**: Our scaffold dictates that if `prompt` is empty, it relies on `source_info` as the clean input, adding an explicit warning flag.

## Retained Clean Examples

### Example 51
- **Task Type**: `Summary`
- **Hallucinated Substring**: `On November 1, 2020,`
- **Raw Dataset Metadata**: `{"total_tokens": 181, "annotation": [[1, 12]]}`
- **Truth Recovery Needs**: Review the `supporting_context_excerpt` within the generated CSV and extract the actual historical or factual answer. Populate it manually into `ground_truth_text_verified`.

### Example 369
- **Task Type**: `Summary`
- **Hallucinated Substring**: `1986 John Hughes film "Pretty in Pink"`
- **Raw Dataset Metadata**: `{"total_tokens": 95, "annotation": [[13, 29]]}`
- **Truth Recovery Needs**: Review the `supporting_context_excerpt` within the generated CSV and extract the actual historical or factual answer. Populate it manually into `ground_truth_text_verified`.

### Example 597
- **Task Type**: `Summary`
- **Hallucinated Substring**: `30 years after the original.`
- **Raw Dataset Metadata**: `{"total_tokens": 40, "annotation": [[32, 40]]}`
- **Truth Recovery Needs**: Review the `supporting_context_excerpt` within the generated CSV and extract the actual historical or factual answer. Populate it manually into `ground_truth_text_verified`.

### Example 93
- **Task Type**: `Summary`
- **Hallucinated Substring**: `2012`
- **Raw Dataset Metadata**: `{"total_tokens": 167, "annotation": [[116, 121]]}`
- **Truth Recovery Needs**: Review the `supporting_context_excerpt` within the generated CSV and extract the actual historical or factual answer. Populate it manually into `ground_truth_text_verified`.

## Allowed Edit Classes
When configuring `corrupted_prompt_candidate` inside the CSV, utilize exactly one of the mapped PRD classes:
- `short_disambiguating_clause`
- `one_added_supporting_evidence_sentence`
- `small_clarification_phrase`
- `format_preserving_rewrite`

## Next Steps (Human Annotation Workflow)
1. **Verify ground truth manually**: Open `outputs/examples_registry.csv` and filter the relevant rows. Extract the factual target from the preserved context fields and commit it to `ground_truth_text_verified`.
2. **Draft corrupted prompts**: Using that verified truth, construct a minimal-edit correction directly in `outputs/examples_registry.csv`. Fill out `corrupted_prompt_candidate`, `edit_class`, and `edit_delta_text`.
3. **Suspend Validation**: Do NOT execute model generators. Await explicit Phase 3 framework deployment to run the structural `clean_reproduction_status` and `corrupted_flip_status` sequences over this CSV.

## Canonical Registry Note
- `outputs/examples_registry.csv` is now the canonical per-example working table.
- `outputs/pair_authoring_review_sheet.csv` remains as an archived source input only.
