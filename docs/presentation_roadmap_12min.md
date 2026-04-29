# 12-Minute Presentation Roadmap

This roadmap is for a 10-12 slide talk. Main slides should carry the story; backup slides should support professor/audience questions without overloading the main talk.

## Main Slides

| Slide | Time | Role | Content |
| --- | ---: | --- | --- |
| 1. Title and Question | 0:45 | Main | Project title, model scope, and central question: can minimal prompt corrections create controlled hallucination/truth pairs for mechanistic tracing? |
| 2. Why This Matters | 0:45 | Main | Hallucinations can look fluent and source-grounded; understanding where a correction changes the model's computation is useful but hard. |
| 3. Problem Setup | 1:10 | Main | Define clean vs. corrupted prompts. Clean means the model reproduces the hallucination; corrupted means a minimal prompt edit flips to verified truth. |
| 4. Workflow Overview | 1:00 | Main | Registry selection, pair validation, forward-pass alignment, layer patching, head patching, and head ablation. Mention run folders for reproducibility. |
| 5. Validation Gate | 1:00 | Main | Explain why examples are traced only if clean reproduces the hallucination and corrupted flips to truth. Mention failed/parked examples are tracked. |
| 6. Example 369 Result | 1:10 | Main | Top layers `L30`, `L29`, `L23`; top heads `L30H26`, `L23H3`; best multi-head ablation `pair_L30H26_L23H3` with score `3.046875`. |
| 7. Example 813 Result | 1:10 | Main | Top layers `L30`, `L29`, `L31`; top head `L29H5`; best single-head ablation `0.257812`; best multi-head ablation `top3_heads` with score `0.179688`. |
| 8. Cross-Example Pattern | 1:15 | Main | The strongest repeated signal is layer-level, not head-level: both examples implicate late layers around `L29-L30`, but exact heads differ. |
| 9. What We Can and Cannot Claim | 1:00 | Main | Can claim two-example pilot evidence for late-layer signal. Cannot claim a stable circuit, stable head, or broad hallucination mechanism. |
| 10. Limitations and Next Steps | 0:55 | Main | Only two completed examples, one model, brittle validation, tokenization issues. Next step is adding more validated examples with the same workflow. |
| 11. Closing Takeaway | 0:50 | Main | The pipeline is now reusable, and the first two examples justify scaling carefully while keeping claims conservative. |

Total main-slide time: about 11:00. The remaining minute in a 12-minute slot is buffer for transitions and brief Q&A.

## Backup / Q&A Slides

| Slide | Role | Content |
| --- | --- | --- |
| B1. Excluded Examples | Backup/Q&A | Concise table of `51`, `3573`, `93`, `597`, `2793`, `2265`, and `2781` with failed/parked/ambiguous reasons. |
| B2. Artifact Workflow | Backup/Q&A | Registry as canonical state; run folders store manifests, summaries, and artifacts. |
| B3. Patching Definitions | Backup/Q&A | Restoration score, ablation score, and prediction-index alignment. |
| B4. Prompt Construction Details | Backup/Q&A | Clean prompt, corrupted prompt, minimal edit, and validation criteria. |
| B5. Full Evidence Table | Backup/Q&A | Rows from `docs/final_deliverable_evidence_table.md`. |

## Speaker Guidance

- Use "pilot evidence" consistently.
- Say "appears in two examples" rather than "the model uses."
- Keep head-level results framed as candidates.
- Present failed and parked examples as part of the methodology, not as hidden failures.
