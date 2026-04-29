# Forward Pass Pilot

## Scope
- Input file: `outputs/tracing_pilot_input.json`
- Model scope: `llama-2-7b-chat` only
- Phase boundary: forward-pass caching only; no activation patching or head-wise tracing yet

## Runtime Summary
- Example ID: `369`
- Output-relative divergence token index: `22`
- Clean absolute divergence token index: `326`
- Clean absolute divergence prediction index: `325`
- Corrupted absolute divergence token index: `650`
- Corrupted absolute divergence prediction index: `649`
- Hallucinated token at divergence: `"` (id `376`)
- Verified-truth token at divergence: `,` (id `29892`)
- Clean divergence index in range: `True`
- Clean prediction index in range: `True`
- Corrupted divergence index in range: `True`
- Corrupted prediction index in range: `True`

## Prompt Summary
- Clean prompt length (tokens): `304`
- Clean output length (tokens): `49`
- Clean total sequence length (tokens): `353`
- Corrupted prompt length (tokens): `628`
- Corrupted output length (tokens): `96`
- Corrupted total sequence length (tokens): `724`

## Tensor Shapes
- Clean logits shape: `[1, 353, 32000]`
- Corrupted logits shape: `[1, 724, 32000]`
- Clean hidden-state count: `33`
- Corrupted hidden-state count: `33`
- Clean hidden-state shapes: `[[1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096], [1, 353, 4096]]`
- Corrupted hidden-state shapes: `[[1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096], [1, 724, 4096]]`
- Clean divergence-prediction logits shape: `[1, 32000]`
- Corrupted divergence-prediction logits shape: `[1, 32000]`

## Output Artifact
- Tensor export: `outputs/forward_pass_pilot.pt`
