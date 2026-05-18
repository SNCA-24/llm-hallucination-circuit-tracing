# LLM Hallucination Circuit Tracing

A pilot mechanistic interpretability workflow for tracing factual hallucination behavior in `llama-2-7b-chat` using validated clean/corrupted prompt pairs, forward-pass alignment, layer patching, head patching, and head ablation.

## Tech Stack Snapshot

- **Language / Core:** Python
- **Modeling / ML:** PyTorch, Hugging Face Transformers, `llama-2-7b-chat`
- **Data / Artifacts:** CSV, JSON, JSONL, pandas, PyYAML
- **Workflow:** CLI scripts, notebooks, run-folder artifacts


## Why This Project Exists

Hallucination work often stops at detection or benchmark scores. This project focuses on a narrower question: once a factual hallucination can be reproduced and then corrected with a minimal prompt intervention, where in the model does that continuation start to change?

The repository builds a controlled tracing workflow around that question. The emphasis is on validation before interpretation: examples are only traced after the original prompt reproduces the target hallucination and a minimally edited prompt flips the continuation toward verified truth.

## What This Project Builds

This repository contains:

- a registry-driven workflow for admitting, reviewing, validating, and tracing candidate hallucination examples
- pair-validation logic for confirming a clean hallucination and a corrected truth flip
- forward-pass tracing that aligns the first divergent output token between clean and corrupted runs
- layer patching, head patching, and head ablation stages for localized intervention analysis
- reproducible run artifacts, summaries, and documentation for completed pilot examples

## Current Pilot Status

| Item | Current state |
|---|---|
| Completed validated examples | `369`, `813` |
| Fully traced through head ablation | `369`, `813` |
| Main repeated finding | Strongest repeated layer-level restoration around `L29-L30` |
| Head-level conclusion | Exact candidate heads differ by example |
| Claim boundary | Pilot evidence only; not a stable circuit claim |

## Architecture / Workflow

```text
Candidate sheets / curated leads
-> outputs/examples_registry.csv
-> token-span feasibility
-> manual clean/corrupted pair authoring
-> pair validation
-> tracing input preparation
-> forward pass alignment
-> layer patching
-> head patching
-> head ablation
-> docs/ findings + outputs/runs/<run_id>/ artifacts
```

### Component Map

| Component | Purpose | Main files |
|---|---|---|
| Registry and workflow state | Canonical per-example state and latest artifact pointers | `outputs/examples_registry.csv`, `src/workflow/run_artifacts.py`, `scripts/build_examples_registry.py` |
| Candidate loading and filtering | Discover upstream rows and narrow to pilot candidates | `src/data/loaders.py`, `src/filtering/pilot_number_subset.py` |
| Pair construction support | Build reviewable records for manual truth recovery and prompt editing | `src/pairs/pair_construction_pilot.py`, `scripts/run_pair_construction_pilot.py` |
| Token-span feasibility | Map labeled hallucinated spans to tokenizer offsets | `src/replay/token_span_check.py`, `scripts/run_token_span_check.py` |
| Pair validation | Confirm clean hallucination reproduction and corrupted truth flip | `src/replay/pair_validation.py`, `scripts/run_pair_validation.py` |
| Tracing stages | Run forward pass, layer patching, head patching, and ablation | `src/tracing/`, `scripts/run_forward_pass_pilot.py`, `scripts/run_layer_patching_pilot.py`, `scripts/run_head_patching_pilot.py`, `scripts/run_head_ablation_pilot.py` |
| Documentation and deliverables | Record findings, limitations, and final reporting artifacts | `docs/` |

## Key Features

- Registry-backed example lifecycle with status flags, latest run pointers, and artifact roots
- Dry-run capable CLI scripts for inspection without rewriting the registry
- Validation gate that rejects tracing attempts unless clean/corrupted behavior is verified
- Teacher-forced divergence alignment for comparing clean and corrected continuations
- Layer patching that measures truth-minus-hallucination margin restoration at the aligned prediction position
- Head patching that ranks candidate attention heads inside top-scoring layers
- Head ablation that tests whether selected heads weaken the hallucinated continuation in the clean run
- Included run manifests, summaries, JSONL outputs, and Markdown findings for completed pilot work

## Technical Implementation

### Core Modules

- `src/workflow/run_artifacts.py`: run IDs, manifests, JSON/JSONL writes, registry updates, selection filters, and artifact lookup
- `src/replay/pair_validation.py`: prompt construction, deterministic generation, substring-based validation checks, and result serialization
- `src/tracing/forward_pass_pilot.py`: teacher-forced sequence construction, divergence detection, hidden-state capture, and forward-pass summary output
- `src/tracing/layer_patching_pilot.py`: corrupted-hidden-state injection into clean runs at the aligned prediction position
- `src/tracing/head_patching_pilot.py`: per-head donor patching within selected layers
- `src/tracing/head_ablation_pilot.py`: zeroing selected head slices to measure clean-run sensitivity

### Execution Flow

1. Candidate examples are admitted into `outputs/examples_registry.csv`.
2. Token mapping checks verify whether the labeled hallucinated span can be traced cleanly at tokenizer resolution.
3. Human-authored clean/corrupted prompt pairs are validated against `llama-2-7b-chat`.
4. Validated pairs are exported into tracing inputs.
5. Forward pass computes the first divergent output token and captures logits and hidden states.
6. Later stages patch corrupted activations into clean runs and then ablate selected heads.
7. Each stage writes run-scoped artifacts under `outputs/runs/<run_id>/`.

### Outputs / Artifacts

- `outputs/examples_registry.csv`: canonical project state
- `outputs/runs/<run_id>/manifest.json`: run metadata and artifact paths
- `outputs/runs/<run_id>/summary.json`: processed/skipped breakdown and run status
- Stage result files such as `pair_validation_results.jsonl`, `layer_patching_results.jsonl`, and `head_ablation_results.jsonl`
- Markdown findings under `docs/` for the two completed pilot examples and the cross-example comparison

### Verification Hooks

- `tests/test_build_examples_registry.py`
- `tests/test_run_artifacts.py`
- CLI `--dry-run` paths for token-span and pair-validation stages

## Data / Inputs / Assumptions

- Primary dataset workflow: `RAGTruth_Xtended`
- Supporting reference dataset: `RAGTruth`
- Configured primary model: `llama-2-7b-chat`
- `mistral-7B-instruct` appears in config for future extension, but current completed results use only `llama-2-7b-chat`.
- Initial feasibility filtering used a small pilot candidate pool; completed tracing results are currently limited to examples 369 and 813.
- External dataset trees such as `RAGTruth-main/` and `RAGTruth_Xtended-main/` are not committed to this repo
- Large forward-pass tensors and model artifacts are intentionally excluded from Git in the public repo

The repo assumes a local or Colab-style environment with separately obtained model access and dataset checkouts. Public documentation and included run summaries are enough to inspect the completed pilot without re-running model code, but full tracing reproduction depends on external assets that are not stored here.

## Methodology / Approach

- Start from candidate examples with a compact hallucinated span suitable for token-level analysis.
- Create a **clean** prompt that reproduces the target hallucination.
- Create a minimally edited **corrupted** prompt that flips the continuation toward verified truth.
- Trace only validated pairs; failed, parked, and ambiguous examples are documented instead of hidden.
- Use teacher-forced clean/corrupted outputs to find the first divergent token.
- Measure **restoration score** during patching as the change in truth-minus-hallucination logit margin.
- Measure **ablation score** as ablated margin minus baseline margin.

This methodology is explicitly pilot-scoped. It is designed to support cautious mechanistic inspection, not broad statistical claims.

## Evaluation / Results

### Pilot Findings

| Example | Validation outcome | Top restoring layers | Top restoring heads | Best ablation result | Interpretation |
|---|---|---|---|---|---|
| `369` | Clean run reproduced hallucination; corrupted run flipped to verified truth | `L30` `16.460938`, `L29` `16.390625`, `L23` `15.804688` | `L30H26`, `L23H3`, `L23H10`, `L29H26`, `L29H5` | Best single head `L23H3` `1.757812`; best multi-head `pair_L30H26_L23H3` `3.046875` | Strong late-layer signal for this example; not a broad mechanism claim |
| `813` | Clean run reproduced hallucination; corrupted run flipped to verified truth | `L30` `8.250000`, `L29` `8.203125`, `L31` `7.875000` | `L29H5`, `L29H21`, `L31H4`, `L31H31`, `L30H31` | Best single head `L29H5` `0.257812`; best multi-head `top3_heads` `0.179688` | Late-layer signal repeats, but head-level pattern differs |

### Cross-Example Takeaway

Both completed examples show the strongest repeated restoration signal in late layers around `L29-L30`. The exact strongest heads differ across examples, which is why the repository does **not** claim a stable head-level hallucination circuit.

## Example Outputs / Run Artifacts

This repository does not ship a UI. The most useful demo artifacts are the included run summaries and findings documents.

Example output from `outputs/runs/20260425_075129_head_ablation_813/head_ablation_summary.md`:

```text
Best single-head ablations
- L29H5: ablation score 0.257812
- L31H4: ablation score 0.164062

Best multi-head ablations
- top3_heads: ablation score 0.179688
```

Useful files to inspect directly:

- `docs/final_deliverable_evidence_table.md`
- `docs/two_example_pilot_comparison.md`
- `docs/pilot_mechanistic_findings_369.md`
- `docs/pilot_mechanistic_findings_813.md`
- `outputs/runs/20260425_064458_forward_pass_813/forward_pass_summary.md`
- `outputs/runs/20260425_075129_head_ablation_813/head_ablation_summary.md`

## Reproducibility / Quickstart

### 1. Environment setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Lightweight local inspection

```bash
python3 scripts/build_examples_registry.py --help
python3 scripts/run_token_span_check.py --example-ids 813 --dry-run
python3 scripts/run_pair_validation.py --config configs/feasibility_pilot.yaml --registry outputs/examples_registry.csv --runs-root outputs/runs --example-ids 813 --dry-run
python3 -m unittest discover -s tests -v
```

### 3. Inspect included pilot outputs

```bash
python3 -m unittest discover -s tests -v
sed -n '1,80p' docs/final_deliverable_evidence_table.md
sed -n '1,120p' docs/two_example_pilot_comparison.md
```

### 4. GPU / Colab-dependent stages

The following stages require model access and practical GPU runtime:

```bash
python3 scripts/prepare_tracing_input.py --registry outputs/examples_registry.csv --runs-root outputs/runs --example-id 813
python3 scripts/run_forward_pass_pilot.py --input outputs/runs/<tracing_prep_run_id>/tracing_pilot_input.json
python3 scripts/run_layer_patching_pilot.py --input-pt outputs/runs/<forward_pass_run_id>/forward_pass_pilot.pt --metadata outputs/runs/<forward_pass_run_id>/tracing_pilot_input_with_divergence.json
python3 scripts/run_head_patching_pilot.py --input-pt outputs/runs/<forward_pass_run_id>/forward_pass_pilot.pt --metadata outputs/runs/<forward_pass_run_id>/tracing_pilot_input_with_divergence.json --layer-results outputs/runs/<layer_patching_run_id>/layer_patching_results.jsonl
python3 scripts/run_head_ablation_pilot.py --input-pt outputs/runs/<forward_pass_run_id>/forward_pass_pilot.pt --metadata outputs/runs/<forward_pass_run_id>/tracing_pilot_input_with_divergence.json --head-patching-results outputs/runs/<head_patching_run_id>/head_patching_results.jsonl
```

## Repository Structure

```text
.
├── configs/                  Pilot configuration
├── data/                     Templates and lightweight auxiliary inputs
├── docs/                     Findings, workflow docs, report draft, and presentation content
├── notebooks/                Thin execution notebooks for each major stage
├── outputs/
│   ├── examples_registry.csv
│   └── runs/                 Run-scoped manifests, summaries, and result files
├── scripts/                  CLI entrypoints for registry, validation, and tracing stages
├── src/                      Reusable Python modules
├── tests/                    Lightweight verification for registry and run-artifact helpers
├── LICENSE
├── THIRD_PARTY_NOTICES.md
├── README.md
└── requirements.txt
```

## Ownership / Project-Owned Work

Project-owned work visible in this repository includes:

- the registry schema and registry rebuild/update workflow
- the token-span, pair-validation, tracing-input, forward-pass, layer-patching, head-patching, and head-ablation scripts
- the reusable workflow helpers under `src/`
- the notebooks, findings docs, report draft, presentation content, and tests included here

This repository does **not** claim ownership of:

- upstream RAGTruth / RAGTruth_Xtended datasets
- Llama 2 model weights or model access
- Hugging Face / PyTorch / pandas / PyYAML and other third-party libraries

This repository contains the project-owned implementation, documentation, and experiment workflow developed for this pilot study. Third-party datasets, model weights, and external libraries remain governed by their original licenses and terms.

## Design Decisions and Tradeoffs

| Decision | Why | Tradeoff / Alternative |
|---|---|---|
| Registry-first workflow | Keeps candidate status, validation state, and latest artifacts in one canonical place | More moving parts than one-off notebooks or ad hoc CSVs |
| Clean/corrupted pair validation before tracing | Prevents tracing examples that never establish a controlled hallucination-to-truth flip | Reduces sample count and slows experimentation |
| Run folders under `outputs/runs/<run_id>/` | Makes each execution auditable and rerunnable with manifests and summaries | More file management than top-level output dumps |
| Deterministic generation settings in config | Keeps pair validation behavior easier to compare across runs | Less exploratory than sampling-heavy generation |
| Layer-first then head-level tracing | Uses coarse localization before fine-grained head inspection | Still single-example and relatively expensive |
| Public repo excludes large tensors and model artifacts | Keeps the repo lightweight and shareable | Full end-to-end reruns require separately generated artifacts and external access |

## Limitations / Honest Scope

- This is a pilot study with only two completed validated examples.
- The current evidence is restricted to `llama-2-7b-chat`; it should not be generalized to other models.
- The strongest repeated signal is late-layer restoration around `L29-L30`, but the head-level candidates differ across examples.
- Failed, parked, and ambiguous examples exist and are documented; the repo does not present only successful traces.
- The public repo does not include large forward-pass `.pt` artifacts, model weights, or full upstream dataset trees.
- This project is not a production hallucination detector, model-serving system, or deployed user-facing product.

### Claim Boundaries

This project demonstrates a reusable tracing workflow and two-example pilot evidence for late-layer restoration. It does **not** claim a stable hallucination circuit, a stable head family, or broad mechanistic generalization.

## Future Improvements

- Add more validated examples through the same registry/tracing workflow and update the report/presentation evidence tables
- Test whether the repeated late-layer signal around `L29-L30` persists across a larger set
- Treat head-level candidates as example-specific until more examples are traced
- Formalize handling for ambiguous token spans and split-token edge cases
- Compare across additional 7B/13B open-weight models after the current pilot is stable

## Skills Demonstrated

### AI / ML

- mechanistic interpretability workflow design
- prompt-based hallucination validation
- teacher-forced sequence alignment
- activation patching and head ablation analysis
- cautious result interpretation and claim-boundary setting

### Data / Analytics

- registry/data-state management for experimental examples
- CSV/JSONL artifact handling
- experiment result summarization and comparison
- traceability from candidate selection to final findings

### Engineering / Systems

- Python CLI workflow design
- reproducible run-artifact management
- configuration-driven execution
- lightweight test coverage for workflow and artifact utilities
- documentation of operational and reproducibility boundaries

### Product / Research Communication

- scoped experiment design for falsifiable clean/corrupted comparisons
- explicit limitation handling instead of success-only reporting
- report- and presentation-ready findings documentation

## License

Original project code, scripts, documentation, and project scaffolding in this repository are licensed under the [MIT License](LICENSE) unless otherwise noted.

Third-party datasets, model checkpoints, model weights, libraries, and other external resources remain governed by their original licenses and terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution and usage notes.
