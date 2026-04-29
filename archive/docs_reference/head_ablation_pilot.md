# Head Ablation Pilot

## Scope
- Retained example ID: `369`
- Model scope: `llama-2-7b-chat` only
- Tested single heads: `L30H26`, `L23H3`, `L23H10`, `L29H26`
- Tested combinations: `[L30H26, L23H3]`, `top 3 heads`, `top 5 heads`
- Phase boundary: destructive head ablation only; no multi-example or broad ablations yet

## Best Single-Head Ablations
- `L23H3`: ablation score `1.757812`, ablated truth logit `14.703125`, ablated hallucinated logit `22.828125`
- `L30H26`: ablation score `1.335938`, ablated truth logit `13.609375`, ablated hallucinated logit `22.156250`
- `L29H26`: ablation score `0.078125`, ablated truth logit `13.039062`, ablated hallucinated logit `22.843750`
- `L23H10`: ablation score `-0.421875`, ablated truth logit `12.570312`, ablated hallucinated logit `22.875000`

## Best Multi-Head Ablations
- `pair_L30H26_L23H3`: ablation score `3.046875`, heads `['L30H26', 'L23H3']`
- `top5_heads`: ablation score `2.664062`, heads `['L30H26', 'L23H3', 'L23H10', 'L29H26', 'L29H5']`
- `top3_heads`: ablation score `2.656250`, heads `['L30H26', 'L23H3', 'L23H10']`

## Hallucination Weakening Check
- Any tested ablation increased truth-minus-hallucination margin: `True`
- Best observed ablation score: `3.046875`

## Output Artifact
- Head ablation results JSONL: `outputs/head_ablation_results.jsonl`
