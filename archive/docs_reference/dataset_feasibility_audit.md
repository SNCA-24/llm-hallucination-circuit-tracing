# Phase 0 Dataset Feasibility Audit

## 1. Config Summary
- Primary Model: llama-2-7b-chat
- Hallucination Target: number

## 2. Repo Discovery Summary
- Discovered Files:
  - RAGTruth_Xtended-main/dataset/rtx/llama-2-7b-chat/llama-2-7b-chat.json
- Chosen File: RAGTruth_Xtended-main/dataset/rtx/llama-2-7b-chat/llama-2-7b-chat.json

## 3. Schema Observations
- Top Level Type: list
- Approx Sample Count: 2965
- Example Keys: id, source_id, temperature, labels, split, quality, response, source, source_info, task_type, prompt, ground_truth

> **Note:** We do not assume `source_info` is the final prompt string. We preserve raw fields and map them to `_candidate` suffixes.

## 4. Record Loading Summary
- Scanned Records: 1001

## 5. Candidate Filtering Summary
- Heuristic Candidates Found: 74
- Pilot Set Size: 10
- Rejections Breakdown:
  - no_labels: 517
  - no_short_numeric_labels: 405
  - multiple_competing_numeric_labels: 5
  - missing_span_data: 0

## 6. Blockers / Uncertainties
- No immediate structural blockers detected.
- Schema Uncertainty: The base dataset does not label 'number hallucination' natively. We use a conservative regex to find digits within short spans.
- Prompt Fields Uncertainty: We have mapped potential inputs to `prompt_candidate` but exact templating format is unverified.

## 7. Errors Encountered
- None.

## 8. Next Recommended Action
- **Proceed to Phase 1/2**: Build minimal-edit pairs (clean vs corrupted) for the exported pilot candidate examples.
