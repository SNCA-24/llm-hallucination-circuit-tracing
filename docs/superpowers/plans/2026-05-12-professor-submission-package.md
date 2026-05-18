# Professor Submission Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a clean professor-facing ZIP bundle from the local repository that preserves code, documentation, and small reproducibility artifacts while excluding heavyweight, secret, or unclear-to-redistribute materials.

**Architecture:** Create a separate `submission_package/` staging tree populated from selected repository files and curated small artifacts. Add package-specific documentation (`README_SUBMISSION.md`, `MANIFEST.md`, `data/README.md`) that explains contents, omissions, dataset provenance, and reproduction boundaries. Verify the staging tree for size, secret patterns, and path hygiene before producing the final ZIP.

**Tech Stack:** Shell utilities (`find`, `rg`, `cp`, `du`, `zip`), Markdown docs, existing repository files

---

### Task 1: Inspect source, datasets, and deliverables

**Files:**
- Create: `docs/superpowers/plans/2026-05-12-professor-submission-package.md`
- Modify: none
- Test: none

- [ ] **Step 1: Inventory candidate inputs**

Run:

```bash
rg --files .
```

Expected: repository file list covering `src/`, `scripts/`, `configs/`, `docs/`, `outputs/`, dataset checkouts, and existing top-level metadata files.

- [ ] **Step 2: Inspect local dataset checkouts and licenses**

Run:

```bash
find . -maxdepth 3 \( -iname 'RAGTruth*' -o -iname '*xtended*' -o -path './data/*' \) | sed -n '1,260p'
```

Expected: local dataset directories and small data templates are visible, enabling a decision on whether redistribution is safe and minimal.

- [ ] **Step 3: Inspect worktree state**

Run:

```bash
git status --short
```

Expected: existing unrelated changes are visible so the packaging work can avoid reverting or overwriting them.

### Task 2: Define professor-facing package contents

**Files:**
- Create: `submission_package/`
- Create: `submission_package/data/`
- Modify: none
- Test: none

- [ ] **Step 1: Decide included repository slices**

Include:

```text
src/
scripts/
configs/
notebooks/ (only lightweight pilot notebooks)
requirements.txt
README.md
LICENSE
THIRD_PARTY_NOTICES.md
selected docs/
selected outputs/
```

Expected: only professor-relevant, reproducibility-relevant material is staged.

- [ ] **Step 2: Decide excluded repository slices**

Exclude:

```text
.git/
.venv/
__pycache__/
wandb/
mlruns/
*.zip
*.tar
*.pt
*.safetensors
HF caches
full raw datasets unless clearly permitted and minimal
```

Expected: no heavyweight or sensitive local-only content enters the package.

### Task 3: Build staging tree

**Files:**
- Create: `submission_package/**`
- Modify: none
- Test: none

- [ ] **Step 1: Remove any prior staging tree and recreate directories**

Run:

```bash
rm -rf submission_package
mkdir -p submission_package/data/curated_examples submission_package/docs submission_package/outputs/runs
```

Expected: a fresh staging tree exists without affecting the source repository.

- [ ] **Step 2: Copy source code and core metadata**

Run:

```bash
cp -R src scripts configs submission_package/
cp requirements.txt README.md LICENSE THIRD_PARTY_NOTICES.md submission_package/
```

Expected: core reproducibility assets are staged.

- [ ] **Step 3: Copy selected notebooks, docs, registry, and run summaries**

Run:

```bash
mkdir -p submission_package/notebooks submission_package/docs submission_package/outputs
```

Expected: destination folders exist for the selected professor-facing materials.

### Task 4: Curate dataset-facing materials

**Files:**
- Create: `submission_package/data/README.md`
- Create: `submission_package/data/curated_examples/**`
- Modify: none
- Test: none

- [ ] **Step 1: Inspect whether upstream local checkouts include license files**

Run:

```bash
find RAGTruth-main RAGTruth_Xtended-main -maxdepth 2 \( -iname 'LICENSE*' -o -iname 'README*' \) 2>/dev/null
```

Expected: license/readme files are available to support redistribution decisions.

- [ ] **Step 2: Prefer a minimal subset if full redistribution is unnecessary**

Create curated subset contents from local lightweight files such as:

```text
data/ragtruth_reproduced_leads_template.csv
outputs/examples_registry.csv
relevant run input/summary JSON or JSONL files for examples 369 and 813
```

Expected: the professor can understand the traced examples without receiving full upstream raw datasets.

- [ ] **Step 3: Document omissions and download instructions**

Write `submission_package/data/README.md` covering:

```text
- upstream dataset locations
- example IDs used
- original license/terms boundaries
- why large/raw datasets are omitted
```

Expected: redistribution boundaries are explicit and defensible.

### Task 5: Add package-specific documentation

**Files:**
- Create: `submission_package/README_SUBMISSION.md`
- Create: `submission_package/MANIFEST.md`
- Test: none

- [ ] **Step 1: Write professor-facing overview**

`README_SUBMISSION.md` must cover:

```text
title
summary
included items
excluded items
environment setup
lightweight local commands
GPU/Colab-only commands
deliverable locations
completed example summaries
limitations
contact info
```

- [ ] **Step 2: Write manifest**

`MANIFEST.md` must enumerate:

```text
included folders/files
excluded folders/files
dataset notes
large artifact notes
```

### Task 6: Verify package and zip it

**Files:**
- Create: `professor_submission_llm_hallucination_tracing.zip`
- Test: `submission_package/**`

- [ ] **Step 1: List the package tree**

Run:

```bash
find submission_package | sort
```

Expected: staged tree matches the professor-facing package design.

- [ ] **Step 2: Scan for oversized files**

Run:

```bash
find submission_package -type f -size +25M -exec stat -f '%z %N' {} \; | sort -nr
```

Expected: either no files over 25 MB or a short justified list.

- [ ] **Step 3: Scan for secret-pattern matches without printing values**

Run:

```bash
rg -n -I --with-filename -e 'HF_TOKEN|OPENAI_API_KEY|api_key|token=|password' submission_package | awk -F: '{print $1":"$2}' | uniq
```

Expected: either no matches or path/line-only warnings for benign code references.

- [ ] **Step 4: Create the final ZIP**

Run:

```bash
zip -r professor_submission_llm_hallucination_tracing.zip submission_package
```

Expected: a local ZIP archive exists for professor submission review.
