# Head Patching Pilot

## Scope
- Input artifact: `outputs/forward_pass_pilot.pt`
- Retained example ID: `369`
- Model scope: `llama-2-7b-chat` only
- Restricted layers: `30`, `29`, `23`
- Phase boundary: head-wise patching only; no ablations yet

## Top Restoring Heads Overall
- Layer `30`, head `26`: restoration score `0.507812`, patched truth logit `13.218750`, patched hallucinated logit `22.593750`
- Layer `23`, head `3`: restoration score `0.453125`, patched truth logit `13.507812`, patched hallucinated logit `22.937500`
- Layer `23`, head `10`: restoration score `0.250000`, patched truth logit `13.257812`, patched hallucinated logit `22.890625`
- Layer `29`, head `26`: restoration score `0.234375`, patched truth logit `13.023438`, patched hallucinated logit `22.671875`
- Layer `29`, head `5`: restoration score `0.187500`, patched truth logit `12.929688`, patched hallucinated logit `22.625000`
- Layer `29`, head `0`: restoration score `0.140625`, patched truth logit `13.179688`, patched hallucinated logit `22.921875`
- Layer `30`, head `31`: restoration score `0.140625`, patched truth logit `13.023438`, patched hallucinated logit `22.765625`
- Layer `29`, head `18`: restoration score `0.101562`, patched truth logit `13.031250`, patched hallucinated logit `22.812500`
- Layer `30`, head `27`: restoration score `0.093750`, patched truth logit `13.054688`, patched hallucinated logit `22.843750`
- Layer `29`, head `9`: restoration score `0.078125`, patched truth logit `13.039062`, patched hallucinated logit `22.843750`

## Top Restoring Heads Per Layer
- Layer `30` best head `26` with restoration score `0.507812`
- Layer `29` best head `26` with restoration score `0.234375`
- Layer `23` best head `3` with restoration score `0.453125`

## Candidate Heads
- Strongest candidate heads from this single-pair pilot: `L30H26, L23H3, L23H10, L29H26, L29H5`

## Output Artifact
- Head results JSONL: `outputs/head_patching_results.jsonl`
