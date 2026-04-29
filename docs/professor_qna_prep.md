# Professor Q&A Prep

## Why only two completed examples?

- Only examples that pass pair validation are traced.
- The workflow requires the clean prompt to reproduce the hallucination and the corrupted prompt to flip to verified truth.
- Several candidates failed or were parked, so the current result is intentionally framed as pilot evidence.

## Why did examples 51 and 3573 fail?

- `51` did not produce a clean validated setup for the pilot after validation.
- `3573` failed because the clean run did not reproduce the target date hallucination and the corrupted run did not flip cleanly.
- These failures are part of the process: failed examples are tracked, not hidden.

## Why does "clean" mean hallucinated and "corrupted" mean corrected?

- "Clean" refers to the original unmodified prompt condition, not to factual correctness.
- "Corrupted" refers to an intervention on the prompt: a minimal edit that changes the model's behavior toward verified truth.
- This naming follows the causal-tracing convention of comparing a baseline run against an intervened run.

## Why focus on layers and heads?

- Layer patching is a coarse localization step: it asks where replacing activations most restores the verified-truth direction.
- Head patching is a finer step inside attention layers: it asks which individual attention heads are candidate contributors.
- Using both gives a staged analysis instead of jumping directly to exact heads.

## What does the layer 29-30 signal mean?

- In both completed examples, the largest layer-level restoration scores appear around late layers `L29-L30`.
- This is the strongest repeated signal across the two examples.
- It is not enough to claim a general mechanism; it is a hypothesis for follow-up examples.

## Why do exact heads differ?

- Head-level effects are more example-specific in the current pilot.
- Example `369` highlights heads such as `L30H26` and `L23H3`.
- Example `813` highlights `L29H5` most strongly.
- This suggests the repeated pattern is currently stronger at the layer level than at the exact-head level.

## Why is example 813's divergence token tokenizer-related?

- The divergence point for `813` lands on token id `29871`, which behaves like a tokenizer boundary / whitespace-like token.
- The meaningful contrast is still between the hallucinated continuation and the verified-truth continuation at the aligned prediction point.
- The decoded token text itself should not be over-interpreted.

## How does activation/layer/head patching work?

- The workflow aligns clean and corrupted outputs under teacher forcing.
- It identifies the causal prediction index immediately before the divergence token.
- Layer patching inserts corrupted-run hidden states into the clean run at the aligned prediction position.
- Restoration is measured as the change in verified-truth-minus-hallucination logit margin.
- The workflow patches one attention head at a time from the corrupted run into the clean run.
- It uses the same aligned prediction position as the layer patching stage.
- Heads are ranked by restoration score.
- Candidate heads are then tested with ablation on the clean run.

## What is the difference between patching and ablation?

- Patching asks whether inserting corrupted-run activations into the clean run restores the verified-truth direction.
- Ablation asks whether removing or suppressing selected clean-run head contributions changes the truth-minus-hallucination margin.
- Patching is mainly for localization; ablation is a follow-up test of candidate component influence.

## Why not claim a stable hallucination circuit yet?

- There are only two fully traced examples.
- Both show late-layer signal, but exact head candidates differ.
- The examples are not enough for statistical generalization or a stable circuit claim.
- The correct framing is pilot evidence and a hypothesis for scaling.

## Why is temperature/reproduction difficult?

- Hallucination reproduction is not guaranteed across runs.
- A prompt can be semantically similar but still fail to reproduce the target hallucination.
- Small prompt changes can alter the generation path, especially around dates, names, and counts.
- That is why validation is a strict gate before tracing.

## How will future examples be added?

- Add or select candidates from `outputs/examples_registry.csv`.
- Validate clean/corrupted behavior.
- Run the same tracing stages into `outputs/runs/<run_id>/`.
- Append the completed example to `docs/final_deliverable_evidence_table.md`.
- Update the ACL report's Results and Cross-Example Analysis sections only after tracing is complete.

## How does the registry/run-folder workflow improve reproducibility?

- `outputs/examples_registry.csv` records the canonical per-example state.
- Each stage writes artifacts, manifests, and summaries under `outputs/runs/<run_id>/`.
- Run folders preserve what was run, which inputs were used, and where outputs landed.
- This makes it easier to resume, audit, and append examples without overwriting prior evidence.

## What is the main result?

- The main pilot result is that both completed examples show strong layer-level causal restoration in late layers around `L29-L30`.
- The exact head candidates differ.
- This is pilot evidence only and should be used to motivate scaling to more examples.
