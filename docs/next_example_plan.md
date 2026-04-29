# Next Example Plan

## Recommendation
- Select a fresh candidate rather than retrying `51`.
- Reason: `51` already failed the validation gate because the clean run did not reproduce the target hallucination, and the corrupted run did not cleanly remove the hallucinated substring.

## Practical Path
1. Reuse the existing feasibility and pair-authoring pipeline to identify the next clean token-localized candidate from the current pool.
2. Author one new minimal corrupted prompt directly in `outputs/examples_registry.csv` using the preserved clean/context/source separation.
3. Rerun pair validation by filtering `outputs/examples_registry.csv` for the next validation target with `llama-2-7b-chat` only.
4. If it validates, pass it through the existing tracing prep, forward-pass, layer patching, head patching, and targeted ablation pipeline unchanged.

## Goal
- Add exactly one more validated example for replication against the existing 369 pilot, without broadening scope or changing the tracing method yet.
