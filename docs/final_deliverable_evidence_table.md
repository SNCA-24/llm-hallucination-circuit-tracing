# Final Deliverable Evidence Table

This table is the source-of-truth summary for the current final presentation and ACL-style report. It should stay conservative: the current evidence is pilot evidence from two validated examples in `llama-2-7b-chat`, not a broad claim about hallucination mechanisms.

Future validated examples can be appended to this same table, then reflected in the report's modular Results section and the presentation only if they change the overall pattern.

| Example | Hallucination / correction target | Validation outcome | Divergence token | Top restoring layers | Top restoring heads | Best ablation result | Conservative interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `369` | Hallucinated full film title: `1986 John Hughes film "Pretty in Pink"`; correction target: `1986 John Hughes film`. | Validated. Clean run reproduced the target hallucination; corrupted run flipped to the verified truth without retaining the hallucinated substring. Full tracing completed. | Output-relative index `22`; hallucinated token `"` (id `376`); verified-truth token `,` (id `29892`). | `L30` (`16.460938`), `L29` (`16.390625`), `L23` (`15.804688`). | `L30H26` (`0.507812`), `L23H3` (`0.453125`), `L23H10` (`0.250000`), `L29H26` (`0.234375`), `L29H5` (`0.187500`). | Best single head: `L23H3` (`1.757812`). Best multi-head: `pair_L30H26_L23H3` (`3.046875`). | Strong pilot evidence that this example has causal restoration signal in late layers, especially `L29-L30`, with a stronger ablation effect than example `813`. Head candidates are example-specific. |
| `813` | Hallucinated charge: `10 counts of fraud`; correction target: `two counts of offering a false instrument for filing in the first degree`. | Validated. Clean run reproduced the target hallucination; corrupted run flipped to the verified truth without retaining the hallucinated substring. Full tracing completed. | Output-relative index `16`; hallucinated divergence token is a tokenizer boundary / whitespace-like token id `29871`; verified-truth token `two` (id `1023`). This tokenization detail should be interpreted carefully. | `L30` (`8.250000`), `L29` (`8.203125`), `L31` (`7.875000`). | `L29H5` (`0.554688`), `L29H21` (`0.140625`), `L31H4` (`0.085938`), `L31H31` (`0.062500`), `L30H31` (`0.054688`). | Best single head: `L29H5` (`0.257812`). Best multi-head: `top3_heads` (`0.179688`). | Strongest signal is again late-layer restoration around `L29-L30`, but ablation effects are smaller and the strongest head differs from `369`. This supports follow-up work, not a stable circuit claim. |

## Current Cross-Example Claim Boundary

Allowed claim: late-layer causal restoration appears in two pilot examples, especially around `L29-L30`.

Not allowed claim: a stable hallucination circuit, stable head family, or general mechanism has been discovered.
