# Pilot Mechanistic Findings: Example 813

## Status
- Validated pair status: retained and validated for the pilot tracing workflow.
- Validation outcome: the clean run reproduced the target hallucination, and the corrupted run flipped to the verified truth without retaining the hallucinated substring.
- Completed tracing stages: forward pass, layer patching, head patching, and head ablation all completed successfully.
- Model scope: `llama-2-7b-chat` only.

## Source Artifacts
- Pair validation: `outputs/runs/20260425_060337_pair_validation_813/`
- Forward pass: `outputs/runs/20260425_064458_forward_pass_813/`
- Layer patching: `outputs/runs/20260425_070723_layer_patching_813/`
- Head patching: `outputs/runs/20260425_073014_head_patching_813/`
- Head ablation: `outputs/runs/20260425_075129_head_ablation_813/`

## Divergence Target
- Output-relative divergence token index: `16`
- Clean absolute divergence token index: `610`
- Clean absolute divergence prediction index: `609`
- Corrupted absolute divergence token index: `640`
- Corrupted absolute divergence prediction index: `639`
- Hallucinated token at divergence: `` (id `29871`)
- Verified-truth token at divergence: `two` (id `1023`)

## Top Restoring Layers
- `L30`: restoration score `8.250000`
- `L29`: restoration score `8.203125`
- `L31`: restoration score `7.875000`

## Top Restoring Heads
- `L29H5`: restoration score `0.554688`
- `L29H21`: restoration score `0.140625`
- `L31H4`: restoration score `0.085938`
- `L31H31`: restoration score `0.062500`
- `L30H31`: restoration score `0.054688`

## Best Ablation Result
- Best single-head ablation: `L29H5` with ablation score `0.257812`
- Best multi-head ablation: `top3_heads` with ablation score `0.179688`
- Tested top-3 setting: `L29H5`, `L29H21`, and `L31H4`
- Interpretation within this pilot: `L29H5` is the strongest individual head candidate for this example, but the ablation effects are much smaller than the strongest layer-patching effects.

## Conservative Interpretation
- This is single-example pilot evidence only.
- The strongest interventions concentrate in late layers, especially `L29` and `L30`, with `L31` also appearing in the top layer/head candidates.
- The head-level evidence points most clearly to `L29H5` for this example, but this should be treated as a candidate component, not a stable mechanism claim.
- The divergence token for this example is a tokenizer-space target token; the empty decoded token text for id `29871` should be interpreted carefully.
- These results are useful for planning follow-up tracing, not for broad claims about the model or hallucination class.
