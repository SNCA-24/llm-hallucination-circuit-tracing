# Head Patching Pilot

## Scope
- Input artifact: `outputs/runs/20260425_064458_forward_pass_813/forward_pass_pilot.pt`
- Retained example ID: `813`
- Model scope: `llama-2-7b-chat` only
- Restricted layers: `30`, `29`, `31`
- Phase boundary: head-wise patching only; no ablations yet

## Top Restoring Heads Overall
- Layer `29`, head `5`: restoration score `0.554688`, patched truth logit `12.210938`, patched hallucinated logit `16.500000`
- Layer `29`, head `21`: restoration score `0.140625`, patched truth logit `11.812500`, patched hallucinated logit `16.515625`
- Layer `31`, head `4`: restoration score `0.085938`, patched truth logit `11.742188`, patched hallucinated logit `16.500000`
- Layer `31`, head `31`: restoration score `0.062500`, patched truth logit `11.750000`, patched hallucinated logit `16.531250`
- Layer `30`, head `31`: restoration score `0.054688`, patched truth logit `11.726562`, patched hallucinated logit `16.515625`
- Layer `29`, head `24`: restoration score `0.039062`, patched truth logit `11.726562`, patched hallucinated logit `16.531250`
- Layer `30`, head `24`: restoration score `0.039062`, patched truth logit `11.664062`, patched hallucinated logit `16.468750`
- Layer `30`, head `30`: restoration score `0.031250`, patched truth logit `11.687500`, patched hallucinated logit `16.500000`
- Layer `31`, head `19`: restoration score `0.023438`, patched truth logit `11.679688`, patched hallucinated logit `16.500000`
- Layer `31`, head `27`: restoration score `0.023438`, patched truth logit `11.726562`, patched hallucinated logit `16.546875`

## Top Restoring Heads Per Layer
- Layer `30` best head `31` with restoration score `0.054688`
- Layer `29` best head `5` with restoration score `0.554688`
- Layer `31` best head `4` with restoration score `0.085938`

## Candidate Heads
- Strongest candidate heads from this single-pair pilot: `L29H5, L29H21, L31H4, L31H31, L30H31`

## Output Artifact
- Head results JSONL: `outputs/runs/20260425_073014_head_patching_813/head_patching_results.jsonl`
