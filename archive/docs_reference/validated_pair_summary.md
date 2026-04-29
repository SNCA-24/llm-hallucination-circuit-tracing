# Validated Pair Summary

## Status
- Retained validated pilot pair count: 1
- Retained example ID: `369`
- This is a single-pair tracing pilot input only, not a final dataset.

## Why 369 Passed
- `clean_reproduction_status` was `reproduced_hallucination`.
- `corrupted_flip_status` was `flipped_to_verified_truth`.
- The corrupted output no longer contained the hallucinated substring.
- The clean run preserved the hallucinated behavior needed for a clean-vs-corrupted tracing comparison.

## Why 51 Was Excluded
- `clean_reproduction_status` was `not_reproduced`, so the clean run did not reproduce the target hallucination.
- `corrupted_flip_status` was `truth_present_but_hallucination_still_present`, so the corrupted run did not cleanly flip away from the hallucinated substring.
- Per the run-1 validation gate, example `51` is parked and not included in `outputs/validated_pairs.jsonl`.

## Evidence Source
- CSV authoring source: `outputs/pair_authoring_review_sheet.csv`
- Validation source: `outputs/pair_validation_results_run1.jsonl`
- Validation narrative: `docs/pair_validation_run1.md`

## Warning
- This export is intentionally narrow. It is only the currently validated pilot pair for tracing-input preparation.
- Do not treat this as a stable benchmark or final professor-ready tracing subset yet.
