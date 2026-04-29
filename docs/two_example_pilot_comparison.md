# Two-Example Pilot Comparison

## Status
- Example `369`: validated pair, forward pass, layer patching, head patching, and head ablation completed for `llama-2-7b-chat`.
- Example `813`: validated pair, forward pass, layer patching, head patching, and head ablation completed for `llama-2-7b-chat`.
- Example `3573`: excluded from this comparison because pair validation failed; it should remain parked/rejected rather than traced.
- In both examples, the clean run reproduced the target hallucination and the corrupted run flipped to the verified truth.
- This document is pilot evidence only. Two examples are not enough to support broad mechanistic claims.

## Source Artifacts
- `813` pair validation: `outputs/runs/20260425_060337_pair_validation_813/`
- `813` forward pass: `outputs/runs/20260425_064458_forward_pass_813/`
- `813` layer patching: `outputs/runs/20260425_070723_layer_patching_813/`
- `813` head patching: `outputs/runs/20260425_073014_head_patching_813/`
- `813` head ablation: `outputs/runs/20260425_075129_head_ablation_813/`
- `369` summary source: `docs/pilot_mechanistic_findings_369.md`

## Layer-Level Comparison
- Example `369` strongest layers: `L30`, `L29`, `L23`
- Example `813` strongest layers: `L30`, `L29`, `L31`
- Common finding: both examples show strong late-layer restoration around `L29` to `L30`.
- Difference: `369` also highlights `L23`, while `813` highlights `L31`.

## Head-Level Comparison
- Example `369` strongest heads: `L30H26`, `L23H3`, with additional support from `L23H10`, `L29H26`, and `L29H5`.
- Example `813` strongest heads: `L29H5`, `L29H21`, `L31H4`, `L31H31`, and `L30H31`.
- The examples overlap more at the layer level than at the exact head level.
- `L29H5` appears in both head-patching result sets, but it is strongest for `813` and only a secondary candidate for `369`.

## Ablation Strength
- Example `369` best single-head ablation: `L23H3` with score `1.757812`.
- Example `369` best multi-head ablation: `pair_L30H26_L23H3` with score `3.046875`.
- Example `813` best single-head ablation: `L29H5` with score `0.257812`.
- Example `813` best multi-head ablation: `top3_heads` with score `0.179688`.
- The ablation effects are substantially stronger for `369` than for `813` under the current pilot settings.

## Conservative Takeaways
- Both examples support continuing to inspect late-layer causal signal around `L29` and `L30`.
- The strongest repeated signal is layer-level, not head-level: both examples implicate late layers around `L29` to `L30`, but the exact heads differ.
- The exact head candidates differ across examples, so the current evidence does not justify claiming a single shared head-level circuit.
- The different ablation strengths suggest that the pilot examples may rely on related late-layer regions with different degrees of concentration in individual heads.
- These results should be treated as a two-example feasibility signal and hypothesis generator only.

## Limitations
- Only two examples have completed the full tracing workflow.
- Both examples use the same model scope, `llama-2-7b-chat`, and should not be generalized to other models.
- The examples differ in target content and tokenization details, so comparisons are qualitative and exploratory.
- More validated examples are needed before making claims about a stable mechanism, layer band, or head family.
