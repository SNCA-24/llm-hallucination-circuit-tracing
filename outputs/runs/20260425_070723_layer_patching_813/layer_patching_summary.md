# Layer Patching Pilot

## Scope
- Input artifact: `outputs/runs/20260425_064458_forward_pass_813/forward_pass_pilot.pt`
- Retained example ID: `813`
- Model scope: `llama-2-7b-chat` only
- Phase boundary: layer-level patching only; no head-wise patching or ablations yet

## Baseline Target-Token Comparison
- Output-relative divergence token index: `16`
- Clean absolute divergence token index: `610`
- Clean absolute divergence prediction index: `609`
- Corrupted absolute divergence token index: `640`
- Corrupted absolute divergence prediction index: `639`
- Hallucinated token at divergence: `` (id `29871`)
- Verified-truth token at divergence: `two` (id `1023`)
- Baseline clean hallucinated-token logit: `16.515625`
- Baseline clean verified-truth-token logit: `11.671875`
- Baseline clean truth-minus-hallucination margin: `-4.843750`

## Top Restoring Layers
- Layer `30`: restoration score `8.250000`, patched truth logit `19.875000`, patched hallucinated logit `16.468750`
- Layer `29`: restoration score `8.203125`, patched truth logit `19.890625`, patched hallucinated logit `16.531250`
- Layer `31`: restoration score `7.875000`, patched truth logit `19.734375`, patched hallucinated logit `16.703125`
- Layer `28`: restoration score `7.828125`, patched truth logit `19.593750`, patched hallucinated logit `16.609375`
- Layer `26`: restoration score `7.812500`, patched truth logit `19.531250`, patched hallucinated logit `16.562500`

## Candidate Layers
- Strongest candidate restoring layers from this single-pair pilot: `30, 29, 31`

## Output Artifact
- Layer results JSONL: `outputs/runs/20260425_070723_layer_patching_813/layer_patching_results.jsonl`
