# Layer Patching Pilot

## Scope
- Input artifact: `outputs/forward_pass_pilot.pt`
- Retained example ID: `369`
- Model scope: `llama-2-7b-chat` only
- Phase boundary: layer-level patching only; no head-wise patching or ablations yet

## Baseline Target-Token Comparison
- Output-relative divergence token index: `22`
- Clean absolute divergence token index: `326`
- Clean absolute divergence prediction index: `325`
- Corrupted absolute divergence token index: `650`
- Corrupted absolute divergence prediction index: `649`
- Hallucinated token at divergence: `"` (id `376`)
- Verified-truth token at divergence: `,` (id `29892`)
- Baseline clean hallucinated-token logit: `22.906250`
- Baseline clean verified-truth-token logit: `13.023438`
- Baseline clean truth-minus-hallucination margin: `-9.882812`

## Top Restoring Layers
- Layer `30`: restoration score `16.460938`, patched truth logit `21.500000`, patched hallucinated logit `14.921875`
- Layer `29`: restoration score `16.390625`, patched truth logit `21.609375`, patched hallucinated logit `15.101562`
- Layer `23`: restoration score `15.804688`, patched truth logit `21.390625`, patched hallucinated logit `15.468750`
- Layer `28`: restoration score `15.570312`, patched truth logit `21.687500`, patched hallucinated logit `16.000000`
- Layer `24`: restoration score `15.546875`, patched truth logit `21.421875`, patched hallucinated logit `15.757812`

## Candidate Layers
- Strongest candidate restoring layers from this single-pair pilot: `30, 29, 23`

## Output Artifact
- Layer results JSONL: `outputs/layer_patching_results.jsonl`
