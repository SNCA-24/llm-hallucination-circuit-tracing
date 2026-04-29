# Final Presentation Slide Content

This is content for a 12-minute presentation. It follows `docs/presentation_roadmap_12min.md` as the base, with one concise validated-pair example slide added for audience clarity.

## Main Slides

### Slide 1. Title and Question

Bullets:
- Pilot mechanistic tracing of prompt-corrected hallucination pairs
- Model scope: `llama-2-7b-chat`
- Core question: can minimal prompt corrections create controlled hallucination/truth pairs for tracing?
- Current evidence: two completed validated examples

Speaker notes:
Introduce the project as a pilot, not a broad mechanistic claim. The main goal is to build a controlled setup where the same model can be compared under a hallucination-reproducing prompt and a minimally corrected prompt. Emphasize that the talk is about the workflow and first two completed tracing cases.

Suggested visual:
- Simple title slide with a clean/corrupted prompt contrast arrow.

### Slide 2. Why This Matters

Bullets:
- Hallucinations can be fluent, plausible, and source-adjacent
- Prompt corrections can change factual behavior
- We want to locate where that change appears in model activations
- The goal is careful pilot evidence, not a production detector

Speaker notes:
Motivate the problem briefly: factual errors are not only surface mistakes; they may reflect different internal continuation preferences. If a minimal prompt correction changes the output, that gives a useful intervention point for causal tracing. Keep the framing narrow: this is a feasibility study for tracing, not a general hallucination solution.

Suggested visual:
- Three-step schematic: hallucinated output -> minimal correction -> verified-truth output.

### Slide 3. Problem Setup

Bullets:
- Clean prompt: original prompt where the model reproduces the hallucination
- Corrupted prompt: minimally edited intervention prompt that flips the model toward verified truth
- Pair is retained only if both conditions validate
- Trace the divergence point between hallucinated and verified continuations

Speaker notes:
Clarify the terminology because it can sound counterintuitive. "Clean" means the unmodified prompt condition, even though its output is hallucinated. "Corrupted" means the intervention condition from the tracing perspective, even though it is more factually correct. The controlled contrast matters more than the name.

Suggested visual:
- Two-row table: clean prompt -> hallucinated target; corrupted prompt -> verified target.

### Slide 4. Workflow Overview

Bullets:
- Registry selects candidates and stores canonical status
- Pair validation gates examples before tracing
- Forward pass aligns clean/corrupted divergence
- Layer patching, head patching, then head ablation

Speaker notes:
Walk through the pipeline at a high level. The important point is that failed examples stop at validation rather than contaminating the tracing evidence. The run-folder architecture is the reproducibility layer behind this workflow: each run preserves artifacts and summaries under `outputs/runs/<run_id>/` so the process can scale beyond one-off notebooks.

Suggested visual:
- Pipeline diagram: registry -> validation -> forward pass -> layer patching -> head patching -> ablation.

### Slide 5. Validation Gate

Bullets:
- Required: clean run reproduces target hallucination
- Required: corrupted run flips to verified truth
- Failed or parked examples are tracked, not hidden
- Only validated examples enter tracing

Speaker notes:
Explain that validation is strict because tracing a failed pair would answer the wrong question. Examples `51` and `3573` failed validation, while other examples were parked or ambiguous. This reduces sample size, but makes the completed evidence cleaner.

Suggested visual:
- Small funnel: candidates -> validated pairs -> traced examples, with failed/parked side bucket.

### Slide 6. Validated Clean/Corrupted Pair Examples

Bullets:
- `369`: clean reproduces `1986 John Hughes film "Pretty in Pink"`; corrupted steers to `1986 John Hughes film`
- `813`: clean reproduces `10 counts of fraud`; corrupted steers to `two counts of offering a false instrument for filing in the first degree`
- Clean = original prompt condition that reproduces the hallucination
- Corrupted = minimal intervention prompt that flips toward verified truth

Speaker notes:
This slide shows the validated contrast, not the entire source context. The exact full prompts are long, so the slide uses abbreviated prompt conditions and exact hallucination/correction targets. Full prompt text and validation artifacts live in the registry and run folders.

Suggested visual:
- Two-row table with columns: Example, Clean/Hallucinated, Corrupted/Verified.

### Slide 7. Example 369 Result

Bullets:
- Target: hallucinated film title vs. verified shorter film reference
- Top restoring layers: `L30`, `L29`, `L23`
- Top heads: `L30H26`, `L23H3`
- Best single-head ablation: `L23H3`, score `1.757812`
- Best multi-head ablation: `pair_L30H26_L23H3`, score `3.046875`

Speaker notes:
Present 369 as the first completed tracing case. It has strong layer-patching scores in late layers and a comparatively strong multi-head ablation result. Keep the interpretation single-example: it identifies candidate components for this case, not a general circuit.

Suggested visual:
- Compact bar chart of top layers and a small callout for best ablation.

### Slide 8. Example 813 Result

Bullets:
- Target: `10 counts of fraud` vs. verified charge phrase
- Top restoring layers: `L30`, `L29`, `L31`
- Strongest head: `L29H5`
- Best single-head ablation: `L29H5`, score `0.257812`
- Best multi-head ablation: `top3_heads`, score `0.179688`

Speaker notes:
Present 813 as the second completed case. It repeats the late-layer pattern but has smaller ablation effects and different strongest head candidates. Note that its divergence token is a tokenizer boundary / whitespace-like token, so the decoded token text should not be over-interpreted. For 813, the top-3 multi-head ablation is weaker than the best single-head ablation, so the selected heads should not be interpreted as combining additively in this pilot run.

Suggested visual:
- Compact table: top layers, top heads, best ablation.

### Slide 9. Cross-Example Pattern

Bullets:
- Both examples share late-layer signal around `L29-L30`
- Exact head candidates differ across examples
- `L29H5` appears in both result sets but has different importance
- `369` has stronger ablation effects than `813`
- Strongest repeated signal is layer-level, not head-level

Speaker notes:
This is the central result slide. The safe claim is that both pilot examples show late-layer causal restoration around `L29-L30`. The unsafe claim would be that a stable head or circuit has been found. Exact heads differ, which is part of the result. `L29H5` appears in both examples, but it has different importance: it is strongest for `813` and only secondary for `369`.

Suggested visual:
- Two-column comparison table for 369 vs. 813 with layer/head/ablation rows.

### Slide 10. What We Can and Cannot Claim

Bullets:
- Can claim: two pilot examples show late-layer restoration around `L29-L30`
- Can claim: exact head candidates differ
- Cannot claim: stable hallucination circuit discovered
- Cannot claim: result generalizes across models or examples
- Current role: hypothesis generator for scaling

Speaker notes:
Make the claim boundary explicit before limitations. The project has enough evidence to justify the workflow and motivate further examples. It does not have enough examples for statistical generalization or a stable mechanism claim.

Suggested visual:
- "Allowed claims" vs. "Not allowed claims" table.

### Slide 11. Limitations and Next Steps

Bullets:
- Only two fully traced examples
- Single model: `llama-2-7b-chat`
- Validation is brittle and prompt-sensitive
- Tokenization can complicate divergence interpretation
- Next: add more validated examples through the same workflow

Speaker notes:
Keep this concise and direct. The limitations are not side notes; they define the correct interpretation. The next step is not to overfit the story to two examples, but to add more validated pairs using the registry/run-folder pipeline.

Suggested visual:
- Limitations/next-steps split table.

### Slide 12. Closing Takeaway

Bullets:
- The workflow now supports reusable validated-pair tracing
- Two completed examples show late-layer restoration around `L29-L30`
- Head candidates differ, so claims remain conservative
- Next evidence should be appended, not retrofitted

Speaker notes:
Close by restating the contribution: a reusable pipeline plus two carefully scoped pilot cases. The strongest result is a repeated late-layer signal, not a discovered circuit. The deliverable should leave the audience with confidence in the workflow and caution about the current sample size.

Suggested visual:
- One-sentence takeaway banner plus small pipeline icon.

## Backup / Q&A Slides

### Backup Slide B1. Excluded Examples

Bullets:
- `51`: failed validation
- `3573`: failed validation; clean did not reproduce and corrupted did not flip cleanly
- `93`, `597`: parked before full validation/tracing
- `2793`: parked because correction target was weak
- `2265`, `2781`: ambiguous token mapping

Speaker notes:
Use this if asked why there are only two completed examples. The answer is that examples were filtered by validation and token-mapping criteria, not selected only after successful tracing.

Suggested visual:
- Compact appendix table with columns: example, status, reason, revisit.

### Backup Slide B2. Patching and Ablation Definitions

Bullets:
- Layer patching: at the aligned prediction position, replace the clean run's layer hidden state with the corrupted run's hidden state
- Purpose: coarse localization of which layers move the model toward the verified-truth token
- Head patching: at the same aligned prediction position, replace one attention head contribution from clean with the corresponding corrupted-run head contribution
- Purpose: identify candidate heads inside the high-scoring layers
- Head ablation: suppress selected candidate head contributions in the clean run
- Purpose: test whether removing those heads weakens the hallucination-favoring direction or increases the truth-minus-hallucination margin

Formula callouts:
```text
truth_margin = verified_truth_token_logit - hallucinated_token_logit

Patching:
baseline_margin = clean_verified_truth_logit - clean_hallucinated_token_logit
patched_margin = patched_verified_truth_logit - patched_hallucinated_token_logit
restoration_score = patched_margin - baseline_margin

Ablation:
baseline_margin = clean_verified_truth_logit - clean_hallucinated_token_logit
ablated_margin = ablated_verified_truth_logit - ablated_hallucinated_token_logit
ablation_score = ablated_margin - baseline_margin
```

Speaker notes:
Use this to answer methodology questions. Patching localizes candidate components by asking what restores the verified-truth direction. Ablation is a follow-up test asking how the clean run changes when candidate head contributions are removed. Positive restoration/ablation score means the intervention increased the model's relative preference for the verified-truth token over the hallucinated token at the selected prediction position.

Suggested visual:
- Three-part method schematic: layer patching -> head patching -> head ablation, plus margin formula callout.

### Backup Slide B3. Registry and Run Artifact Workflow

Bullets:
- `outputs/examples_registry.csv` is canonical project state
- Routine artifacts live under `outputs/runs/<run_id>/`
- Each run has `manifest.json` and `summary.json`
- Registry stores concise status, not raw artifacts
- Design supports reruns, partial failures, and future examples

Speaker notes:
Use this to explain reproducibility. The registry keeps the current status per example, while run folders preserve exactly what each stage produced. This avoids overwriting evidence and makes future examples append-only.

Suggested visual:
- Folder tree: registry plus run folders with manifests and summaries.

### Backup Slide B4. Full Evidence Table

Bullets:
- `369`: top layers `L30`, `L29`, `L23`; single `L23H3` `1.757812`; multi `pair_L30H26_L23H3` `3.046875`
- `813`: top layers `L30`, `L29`, `L31`; single `L29H5` `0.257812`; multi `top3_heads` `0.179688`
- Shared: late-layer restoration around `L29-L30`
- Difference: exact head candidates and ablation strength
- Evidence is pilot-stage only

Speaker notes:
Use this when asked for exact numbers. Keep the focus on comparison rather than every score. The full source table is `docs/final_deliverable_evidence_table.md`.

Suggested visual:
- Condensed version of the final evidence table.

### Backup Slide B5. Q&A Support

Bullets:
- Why only two? Strict validation gate
- Why clean/corrupted? Original run vs. intervention run terminology
- Why `L29-L30`? Repeated strongest layer-level signal
- Why no circuit claim? Too few examples and heads differ
- How to scale? Append validated examples through registry/run folders

Speaker notes:
Use this as a quick support slide for broad questions. The core answer should stay the same: the work is a careful pilot that found a repeated late-layer signal, but not enough evidence for a stable circuit or head-level claim.

Suggested visual:
- Five-question Q&A grid.
