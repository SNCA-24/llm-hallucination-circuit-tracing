# llm-hallucination-circuit-tracing

Pilot mechanistic interpretability study tracing layer/head signals in prompt-corrected LLM hallucination pairs.

## Summary

This repository contains the code, registry workflow, saved summaries, and final deliverable drafts for a pilot study on factual hallucinations in `llama-2-7b-chat`. The project builds validated clean/corrupted prompt pairs, then uses forward-pass alignment, layer patching, head patching, and head ablation to inspect where the model's continuation shifts from a hallucinated target toward a verified-truth target.

The current result is pilot evidence only. It should not be presented as a stable hallucination circuit, a stable head family, a production hallucination detector, or a result that generalizes across models or example classes.

## Professor-Aligned Objective

The objective is to localize layers and attention heads that contribute to hallucinated continuations under a controlled prompt intervention. The workflow emphasizes careful validation before tracing: an example is traced only when the original prompt reproduces the hallucination and a minimal intervention prompt flips the model toward the verified truth.

## Current Pilot Status

- Completed validated examples: `369` and `813`
- Fully traced examples through head ablation: `369` and `813`
- Failed or parked examples are documented rather than hidden.
- Main pilot finding: both completed examples show strongest repeated layer-level restoration around `L29-L30`.
- Head-level finding: exact head candidates differ across examples; no stable head-level circuit is claimed.

## Workflow Overview

1. Candidate examples are admitted and tracked in `outputs/examples_registry.csv`.
2. Pair validation confirms the clean hallucination and corrupted truth flip.
3. Forward-pass alignment identifies the causal prediction index at the divergence point.
4. Layer patching localizes coarse layer-level restoration signal.
5. Head patching ranks candidate attention heads inside high-scoring layers.
6. Head ablation tests selected candidate heads in the clean run.
7. Final summaries and deliverables remain in `docs/`.

Routine run artifacts are stored under `outputs/runs/<run_id>/`. Large tensor/model artifacts are intentionally excluded from Git.

## Repository Structure

```text
configs/                  Configuration files for pilot scripts
data/                     Lightweight templates and approved auxiliary inputs
docs/                     Stable process docs, findings, report draft, and slide content
notebooks/                Thin Colab/local execution wrappers
outputs/examples_registry.csv
                          Canonical project registry
outputs/runs/             Run metadata and small summaries; large tensors ignored
scripts/                  CLI entrypoints for registry, validation, and tracing stages
src/                      Reusable Python implementation
tests/                    Lightweight unit tests for registry/run helpers
archive/                  Legacy reference material retained for provenance
```

External dataset checkouts such as `RAGTruth-main/` and `RAGTruth_Xtended-main/` are intentionally ignored and should be downloaded separately when needed.

## Local Lightweight Reproduction

Create an environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Useful lightweight checks:

```bash
python3 scripts/build_examples_registry.py --help
python3 scripts/run_token_span_check.py --example-ids 813 --dry-run
python3 scripts/run_pair_validation.py --example-ids 813 --dry-run
python3 -m pytest tests
```

Registry rebuilds preserve live experiment state by default. Use `--reset` only when intentionally discarding live registry state and returning to source-sheet defaults.

## GPU / Colab Steps

The following stages require a GPU/Colab-style runtime for practical execution with `llama-2-7b-chat`:

- pair validation with model generation,
- forward pass tensor capture,
- layer patching,
- head patching,
- head ablation.

The run-folder workflow records manifests, summaries, and small result files where useful. Large `.pt`, `.safetensors`, model weight, and cache artifacts are not committed.

## Final Deliverables

Key deliverable files:

- `docs/final_presentation_slide_content.md`
- `docs/acl_report_draft.md`
- `docs/final_deliverable_evidence_table.md`
- `docs/professor_qna_prep.md`
- `docs/two_example_pilot_comparison.md`
- `docs/pilot_mechanistic_findings_369.md`
- `docs/pilot_mechanistic_findings_813.md`

The documentation index is in `docs/README.md`.

## Reproducibility Notes

- `outputs/examples_registry.csv` is the canonical project state.
- `outputs/runs/<run_id>/manifest.json` and `summary.json` record completed run metadata.
- Large tensor artifacts are intentionally excluded from Git and can be regenerated from the scripts when the model/runtime is available.
- Future examples should be appended through the registry workflow and reported by adding rows/subsections rather than rewriting the current two-example interpretation.

## Claim Boundaries

Allowed:

- Two validated pilot examples show late-layer restoration around `L29-L30`.
- Exact head candidates differ across examples.
- The workflow is reusable for adding more validated examples.

Not allowed:

- A stable hallucination circuit has been discovered.
- A stable head family has been discovered.
- Results generalize across models or example classes.
- This is a production-ready hallucination detector.

## Future Work

- Add more validated examples through the registry workflow.
- Track whether late-layer signal around `L29-L30` persists.
- Treat head-level candidates as example-specific until more examples are traced.
- Convert report references to BibTeX and generate the final presentation deck.

## License

Original project code, scripts, documentation, and project scaffolding in this repository are licensed under the [MIT License](LICENSE) unless otherwise noted.

Third-party datasets, model checkpoints, model weights, libraries, and other external resources remain governed by their original licenses and terms. This repository does not relicense upstream materials such as RAGTruth, RAGTruth_Xtended, Llama-2 artifacts, or external Python dependencies under MIT.

Large model artifacts are not included in this repository. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for additional attribution and usage notes.
