# Next-Round Review Top 3

## Scope
- Retained clean-mapped examples only: `2793`, `813`, `3573`
- Excluded from this manual-review sheet: `2265`, `2781` because their token mappings were ambiguous
- Phase boundary: manual review prep only; no validation or tracing yet
- Going forward, scripts should read `outputs/examples_registry.csv`; this top-3 sheet is an archived source input.

## Why These Three Were Kept
- `2793`: Single unsupported year token with a clean token map. It is compact, likely lexical, and should be straightforward to truth-verify and minimally edit.
- `813`: Clear number/count conflict with a clean token map. The mismatch is concrete and localized, which makes it a strong validation candidate.
- `3573`: Invented full calendar date with a clean token map. It stays in the preferred date/year regime while remaining short and interpretable.

## Preserved Fields
- Prompt/context separation is preserved via `raw_prompt_field`, `raw_source_info_field`, and `clean_input_text_for_validation`.
- Hallucinated span metadata is preserved via `hallucinated_substring`, `hallucinated_char_span`, `hallucinated_token_span`, and `first_hallucinated_token_index`.
- Token mapping status is now locked as `clean` for all three retained examples.

## Manual Fields Left Blank
- `ground_truth_text_verified`
- `corrupted_prompt_candidate`
- `edit_class`
- `edit_delta_text`
- `why_minimal`
- `semantic_equivalence_check`
- `reviewer_notes`
