# Next Round Batch: Fresh Review Five

## Scope
- Retained fresh-review IDs only: `2265`, `2781`, `3573`, `2793`, `813`
- Excluded from this batch by instruction: `93`, `597`, `75`, `2439`
- Phase boundary: review and validation prep only; no tracing runs yet

## Artifact Notes
- `outputs/next_round_batch_5.jsonl` preserves raw prompt vs raw source/context separation for each retained example.
- The canonical working table is now `outputs/examples_registry.csv`.
- `outputs/next_round_review_sheet.csv` is retained as an archived source input and migration checkpoint only.
- Hallucinated span fields are preserved from the dataset labels.
- Token-span status is included as a triage field. None of these five were in the earlier 10-example token-feasibility pass, so all five still need token mapping checks.

## Retained Candidates
| Example ID | Category | Hallucinated Substring | Token Mapping Status | Why Shortlisted |
| --- | --- | --- | --- | --- |
| `2265` | date/year | `April 2019` | needs_checking | Month-year added where the source only supports the month so the correction path should stay local |
| `2781` | date/year | `Gao was detained in April 2013` | needs_checking | Specific year anchor was added to an otherwise supported event which should permit a short corrective edit |
| `3573` | date/year | `On Saturday, April 10` | needs_checking | Full calendar date appears to be invented and should localize to a short temporal span |
| `2793` | date/year | `2020` | needs_checking | Single future-year insertion is compact and likely to yield a clean lexical divergence |
| `813` | number/count | `10 counts of fraud` | needs_checking | Clear numeric conflict versus the source and the correction should stay tightly localized |

## Manual Fields Left Blank
- `ground_truth_text_verified`
- `corrupted_prompt_candidate`
- `edit_class`
- `edit_delta_text`
- `why_minimal`
- `semantic_equivalence_check`
- `clean_reproduction_status`
- `corrupted_flip_status`
- `reviewer_notes`
