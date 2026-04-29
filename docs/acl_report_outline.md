# ACL-Style Modular Report Outline

Working title: **Pilot Mechanistic Tracing of Prompt-Corrected Hallucination Pairs in Llama-2-7B-Chat**

This is an outline only, not the full report. Keep every results claim pilot-scoped unless additional validated examples are added.

## Abstract

- One-paragraph summary of the problem, setup, model scope, two completed examples, and main pilot finding.
- State that both validated examples show late-layer restoration around `L29-L30`, while exact heads differ.
- Avoid claiming a discovered mechanism.

## 1. Introduction

- Motivation: hallucinations can persist even when source context is available.
- Project question: can minimal prompt corrections create controlled clean/corrupted pairs suitable for mechanistic tracing?
- Contribution framing:
  - registry-based workflow for selecting and tracking examples,
  - validated clean/corrupted pair construction,
  - pilot tracing evidence from two examples,
  - conservative cross-example comparison.

## 2. Related Work

- Hallucination and factuality in language models.
- Activation patching and causal tracing.
- Prompt sensitivity and controlled interventions.
- Scope note: this project uses prior methods as tools; it does not claim a new tracing algorithm.

## 3. Dataset and Model Scope

- Source examples come from the project registry, `outputs/examples_registry.csv`.
- Model scope is `llama-2-7b-chat` only.
- Completed examples: `369` and `813`.
- Failed or parked examples are tracked separately rather than excluded silently.

## 4. Methodology

### 4.1 Registry and Run Artifact Workflow

- Explain the registry as canonical state.
- Explain run folders under `outputs/runs/<run_id>/`.
- Explain why manifests, summaries, and artifacts are separated from stable docs.

### 4.2 Clean/Corrupted Pair Construction

- Clean prompt: original validation prompt where the model reproduces the target hallucination.
- Corrupted prompt: minimally edited prompt that steers the model to the verified truth.
- Validation requirement: clean reproduces hallucination and corrupted flips to truth.

### 4.3 Forward-Pass Alignment

- Teacher-forced prompt and output alignment.
- Causal prediction index is computed from the validated divergence point.
- No example ID should be hardcoded in the tracing workflow.

### 4.4 Layer Patching

- Patch corrupted-run hidden states into the clean run at the aligned prediction position.
- Restoration score uses truth-minus-hallucination logit margin change.

### 4.5 Head Patching and Head Ablation

- Head patching evaluates one attention head at a time.
- Head ablation tests candidate heads in the clean run.
- Ablation score is ablated margin minus baseline margin.

## 5. Experimental Setup

- Hardware/runtime: Colab runs for heavy model stages where applicable.
- Artifacts: per-stage run folders with manifests and summaries.
- Selection criteria: validated pair only; failed or parked examples are not traced.
- Evaluation quantities:
  - validation status,
  - divergence token,
  - top restoring layers,
  - top restoring heads,
  - best ablation result.

## 6. Results

Results are reported as pilot evidence over validated examples, not as statistical generalization.

### 6.1 Example 369

- Summarize validation outcome.
- Report divergence token.
- Report top layers: `L30`, `L29`, `L23`.
- Report top heads: `L30H26`, `L23H3`, `L23H10`, `L29H26`, `L29H5`.
- Report best ablation: `pair_L30H26_L23H3`, score `3.046875`.
- Interpretation: strong single-example signal, not a broad claim.

### 6.2 Example 813

- Summarize validation outcome.
- Report divergence token.
- Report top layers: `L30`, `L29`, `L31`.
- Report top heads: `L29H5`, `L29H21`, `L31H4`, `L31H31`, `L30H31`.
- Report best ablation: `top3_heads`, score `0.179688`; best single head `L29H5`, score `0.257812`.
- Interpretation: late-layer signal repeats, but head-level pattern differs.

### 6.3 Future Example N

- Placeholder subsection for future validated examples.
- Use the same fields as examples `369` and `813`.
- Add only after pair validation and tracing complete.

## 7. Cross-Example Analysis

- Compare validated pair status.
- Layer-level overlap: both examples implicate `L29-L30`.
- Head-level differences: exact strongest heads differ.
- Ablation strength differences: `369` shows substantially stronger ablation effects than `813`.
- Main conservative takeaway: the strongest repeated signal is layer-level, not head-level.

## 8. Discussion

- Why the clean/corrupted setup is useful for controlled tracing.
- Why late-layer effects are plausible but not yet general.
- Why exact head differences matter.
- How the registry/run workflow reduces repeated work and helps scale the pilot.

## 9. Limitations

- Only two fully traced examples.
- Single model: `llama-2-7b-chat`.
- Prompt validation is brittle and temperature-sensitive.
- Tokenization can make divergence targets hard to interpret.
- Failed and parked examples show that validation is not automatic.
- Current evidence does not establish a stable circuit or broad hallucination mechanism.

## 10. Ethical Considerations

- The project studies factuality failures and corrections; it should not be presented as a production hallucination detector.
- Generated summaries may contain sensitive or misleading claims if used outside the controlled research context.
- Avoid overstating interpretability findings in ways that imply model behavior is fully understood or controlled.

## 11. Conclusion

- Restate the pilot result: two validated examples show late-layer restoration around `L29-L30`.
- Emphasize that head-level candidates differ and claims remain limited.
- State next step: add more validated examples using the same registry/run workflow.

## References

- Placeholder for work on hallucination, factuality, activation patching, causal tracing, and prompt sensitivity.

## Appendix

### A. Registry Workflow

- Canonical registry fields.
- Run folder schema.
- How examples move from candidate to validation to tracing completion.

### B. Excluded Examples

- Use `docs/excluded_examples_summary.md` as the source.
- Include failed, parked, and ambiguous examples.

### C. Run Artifact Table

- Table of validation, forward pass, layer patching, head patching, and head ablation run folders.
- Include manifest and summary paths where relevant.

### D. Prompt Construction Details

- Clean prompt template.
- Corrupted prompt edit class.
- Minimal edit rationale.
- Validation prompt-building logic.

### E. Per-Example Detailed Results

- Expanded tables from `docs/final_deliverable_evidence_table.md`.
- Optional JSONL artifact references.
