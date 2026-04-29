# Head Ablation Pilot

## Scope
- Retained example ID: `813`
- Model scope: `llama-2-7b-chat` only
- Tested single heads: `L29H5`, `L29H21`, `L31H4`, `L31H31`, `L30H31`
- Tested combinations: `pair_L29H5_L29H21`, `top3_heads`, `top5_heads`
- Phase boundary: destructive head ablation only; no multi-example or broad ablations yet

## Best Single-Head Ablations
- `L29H5`: ablation score `0.257812`, ablated truth logit `12.007812`, ablated hallucinated logit `16.593750`
- `L31H4`: ablation score `0.164062`, ablated truth logit `12.132812`, ablated hallucinated logit `16.812500`
- `L30H31`: ablation score `0.000000`, ablated truth logit `11.656250`, ablated hallucinated logit `16.500000`
- `L31H31`: ablation score `-0.023438`, ablated truth logit `11.648438`, ablated hallucinated logit `16.515625`

## Best Multi-Head Ablations
- `top3_heads`: ablation score `0.179688`, heads `['L29H5', 'L29H21', 'L31H4']`
- `top5_heads`: ablation score `0.164062`, heads `['L29H5', 'L29H21', 'L31H4', 'L31H31', 'L30H31']`
- `pair_L29H5_L29H21`: ablation score `-0.007812`, heads `['L29H5', 'L29H21']`

## Hallucination Weakening Check
- Any tested ablation increased truth-minus-hallucination margin: `True`
- Best observed ablation score: `0.257812`

## Output Artifact
- Head ablation results JSONL: `outputs/runs/20260425_075129_head_ablation_813/head_ablation_results.jsonl`
