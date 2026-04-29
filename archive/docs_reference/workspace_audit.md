# Workspace Audit

## Current Workspace Tree
- `Professor Aligned PRD v4.md` (Source of truth)
- `RAGTruth-main/` (Local RAGTruth dataset repository)
- `RAGTruth_Xtended-main/` (Local RAGTruth_Xtended dataset repository)
- `legacy_files/` (Previous iterations and older files)
- Newly created implementation directories: `src/`, `docs/`, `scripts/`, `notebooks/`, `configs/`, `outputs/`, `tests/`

## Canonical Project Root
The main implementation root for our work should be the directory where all these components currently reside (`<project-root>`). This overarching directory contains the relevant dataset submodules and will handle the code for our interpretability tracing pipeline. 

## Dataset References
The existing dataset repositories (`RAGTruth-main` and `RAGTruth_Xtended-main`) must remain untouched and read-only.
- They should **not** be refactored or modified. 
- They should be referenced via configuration files (e.g., in `configs/`) using paths relative to this project root. 
- During `Phase 1`, data loading scripts in `src/data/` will read from these repositories, perform extraction/filtering, and save the resulting derived tracing subsets into our own `outputs/` folder.

## Missing Pieces Needed Before Phase 0
According to the PRD, the following decisions are not yet locked down and must be confirmed to exit Phase 0 (Feasibility phase):
1. **The first hallucination type to lock:** (e.g., number, date, or short entity).
2. **The exact target model/checkpoint:** Must be open-weight, compatible with tracing tools, and runnable within budget.
3. **The exact dataset starting point:** Whether to use RAGTruth_Xtended as the primary base or another.
4. **Allowed corrupted-prompt edit policy:** The precise minimal edit rules for correcting prompts (e.g., add a phrase, short disambiguation).
