# Implementation Bootstrap

## PRD Phase to Code Module Mapping

Based on the Professor-Aligned PRD, here is how the experimental phases map to our source code structure:

- **Phase 0 (Feasibility):** Managed via settings in `configs/` and initial probing scripts in `notebooks/`.
- **Phase 1 (Data Curation):** `src/filtering/`
- **Phase 2 (Clean/Corrupted Pair Construction):** `src/pairs/`
- **Phase 3 (Replay & Token Alignment):** `src/replay/`
- **Phase 4 & 5 (Layer-Level & Head-Level Tracing):** `src/tracing/`
- **Phase 6 & 7 (Causal Verification & Cross-Type Comparison):** `src/tracing/` and `src/reporting/`

## Folder Responsibilities

- **Dataset Loading (`src/data/`):** Responsible for parsing the untouched base datasets (RAGTruth / RAGTruth_Xtended) without modifying them.
- **Tracing Subset Creation (`src/filtering/`):** Implements the strict inclusion/exclusion criteria to extract a high-purity tracing subset.
- **Clean/Corrupted Pair Construction (`src/pairs/`):** Applies the minimal-edit policy to generate corrected prompts and validates their semantic equivalence.
- **Replay Checks (`src/replay/`):** Maps character spans to exact tokens, identifies the first divergent token, measures token-level logprobs, and validates dataset replay fidelity (exact generation vs teacher-forced).
- **Layer/Head Tracing (`src/tracing/`):** The core causal tracing loop. Implements activation caching, layer-wise restorative patching, head-wise patching, and destructive ablation logic.
- **Reports/Plots (`src/reporting/`):** Aggregates findings, computes causal effect sizes, and generates layer/head ranking visualizations.
- **Utilities (`src/utils/`):** Shared utilities like tokenizer manipulation helpers, logging formatters, and file I/O operations.

## Next 3 Implementation Steps
1. **Define Config Schema:** Create a base YAML or JSON configuration file in `configs/` to formalize the paths to our dataset repositories, the model choice, and the edit policies.
2. **Create Dataset Loader:** Write a simple, read-only loader in `src/data/` to ingest a small sample of our base dataset in the required schema for our pilot.
3. **Sub-Sample Pilot:** Write a script using `src/filtering/` to output 5-10 clean hallucination examples based on predefined criteria to validate token mapping feasibility.
