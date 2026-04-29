# Tracing Pilot Prep

## Status
- Retained tracing pilot pair count: 1
- Retained example ID: `369`
- This is a single-pair pilot only, not a final dataset.

## Fields Ready Now
- `example_id`
- `clean_input_text_for_validation`
- `corrupted_prompt_candidate`
- `built_clean_prompt`
- `built_corrupted_prompt`
- `ground_truth_text_verified`
- `hallucinated_substring`
- `hallucinated_char_span`
- `hallucinated_token_span`
- `first_hallucinated_token_index` (legacy dataset span index; no longer the tracing target)
- `model_output_clean`
- `model_output_corrupted`
- `edit_class`
- `edit_delta_text`
- `why_minimal`

## Validated Divergence Target
- The tracing target should now be the first divergent token position between:
  - `model_output_clean`
  - `model_output_corrupted`
- After rerunning the forward-pass pilot, the tracing prep artifact should also contain:
  - `validated_divergence_token_index`
  - `hallucinated_token_id_at_divergence`
  - `verified_truth_token_id_at_divergence`
  - `hallucinated_token_text_at_divergence`
  - `verified_truth_token_text_at_divergence`

## What Still Needs To Be Computed During Tracing
- Exact forward-pass activations for the clean and corrupted runs
- Token-level hidden-state caches at the validated divergence token position
- Logit comparisons at the divergent token readout
- Layer-wise patching inputs and outputs
- Head-wise causal effect measurements
- Any optional ablation or restoration checks

## Scope Warning
- This prep file is intentionally narrow and is only meant to feed the first tracing pilot.
- Do not treat this as a stable benchmark, final tracing subset, or multi-example dataset yet.
- No activation patching or tracing logic is implemented here.
