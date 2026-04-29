# Pilot Mechanistic Findings: Example 369

## Status
- Validated pair status: retained and validated for the single-pair pilot.
- Validation outcome: the clean run reproduced the target hallucination, and the corrupted run flipped to the verified truth without retaining the hallucinated substring.
- Model scope: `llama-2-7b-chat` only.

## Divergence Target
- Output-relative divergence token index: `22`
- Clean absolute divergence token index: `326`
- Clean absolute divergence prediction index: `325`
- Corrupted absolute divergence token index: `650`
- Corrupted absolute divergence prediction index: `649`
- Hallucinated token at divergence: `"` (id `376`)
- Verified-truth token at divergence: `,` (id `29892`)

## Top Restoring Layers
- `L30`: restoration score `16.460938`
- `L29`: restoration score `16.390625`
- `L23`: restoration score `15.804688`

## Top Restoring Heads
- `L30H26`: restoration score `0.507812`
- `L23H3`: restoration score `0.453125`
- `L23H10`: restoration score `0.250000`
- `L29H26`: restoration score `0.234375`
- `L29H5`: restoration score `0.187500`

## Best Ablation Result
- Best single-head ablation: `L23H3` with ablation score `1.757812`
- Best multi-head ablation: `pair_L30H26_L23H3` with ablation score `3.046875`
- Interpretation within this pilot: ablating `L30H26` and `L23H3` together most strongly increased the truth-minus-hallucination margin on the clean run at the validated divergence prediction position.

## Boundary
- This is single-example pilot evidence only.
- It is useful for scoping the tracing approach and identifying concrete candidate components.
- It is not yet a broad claim about the model, the hallucination type, or a stable mechanism class.
