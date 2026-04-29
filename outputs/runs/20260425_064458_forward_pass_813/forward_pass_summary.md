# Forward Pass Pilot

## Scope
- Input file: `outputs/runs/20260425_013328_tracing_prep_813/tracing_pilot_input.json`
- Model scope: `llama-2-7b-chat` only
- Phase boundary: forward-pass caching only; no activation patching or head-wise tracing yet

## Runtime Summary
- Example ID: `813`
- Output-relative divergence token index: `16`
- Clean absolute divergence token index: `610`
- Clean absolute divergence prediction index: `609`
- Corrupted absolute divergence token index: `640`
- Corrupted absolute divergence prediction index: `639`
- Hallucinated token at divergence: `` (id `29871`)
- Verified-truth token at divergence: `two` (id `1023`)
- Clean divergence index in range: `True`
- Clean prediction index in range: `True`
- Corrupted divergence index in range: `True`
- Corrupted prediction index in range: `True`

## Prompt Summary
- Clean prompt length (tokens): `594`
- Clean output length (tokens): `95`
- Clean total sequence length (tokens): `689`
- Corrupted prompt length (tokens): `624`
- Corrupted output length (tokens): `95`
- Corrupted total sequence length (tokens): `719`

## Tensor Shapes
- Clean logits shape: `[1, 689, 32000]`
- Corrupted logits shape: `[1, 719, 32000]`
- Clean hidden-state count: `33`
- Corrupted hidden-state count: `33`
- Clean hidden-state shapes: `[[1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096], [1, 689, 4096]]`
- Corrupted hidden-state shapes: `[[1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096], [1, 719, 4096]]`
- Clean divergence-prediction logits shape: `[1, 32000]`
- Corrupted divergence-prediction logits shape: `[1, 32000]`

## Output Artifact
- Tensor export: `outputs/runs/20260425_064458_forward_pass_813/forward_pass_pilot.pt`
