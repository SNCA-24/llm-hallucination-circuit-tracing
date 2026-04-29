# RAGTruth Leads Policy

## What A Reproduced Lead Is
A reproduced lead is a manually reviewed RAGTruth response that appears to reproduce a target hallucination closely enough to be useful as an upstream clue for finding or confirming an accepted example.

## Role Of Leads
- Leads are only one source of candidates.
- They do not replace direct exploration from RAGTruth_Xtended.
- They do not automatically become tracing examples.

## Where To Store Leads
- Store leads in a separate sheet such as `data/ragtruth_reproduced_leads.csv`.
- Keep the lead sheet distinct from `outputs/examples_registry.csv`.
- The lead sheet is for pre-registry triage and provenance capture.

## Matching Standard
- Prefer response-level matching over weak source-only matching.
- A lead is stronger when the reproduced response clearly matches the target behaviour, span, and surrounding semantics.
- Source-only similarity is not enough when response behaviour diverges materially.

## Rejection Before Registry Admission
Reject a lead before registry admission when:
- the response match is weak or ambiguous
- the example cannot be matched confidently to an accepted substrate row
- the hallucination is diffuse, approximation-heavy, or multi-span
- the lead introduces scientific uncertainty that weakens the later tracing interpretation

Such rows should remain outside the registry or be labeled as rejected in the lead sheet.

Warning: Use `--allow-new-lead-rows` only after a lead has already passed pre-registry checks and has been manually approved for registry admission.

## Temperature Policy
- Temperature is provenance and triage metadata only.
- Preserve it when a lead is confidently matched and the metadata is available.
- Do not treat temperature as proof of exact behavioural equivalence.
- Do not weaken pair validation or tracing gates just because temperature metadata is known.
