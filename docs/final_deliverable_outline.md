# Final Deliverable Outline

This file connects the 12-minute presentation roadmap, the ACL-style report outline, and the evidence table. The goal is to keep the final deliverables modular so new validated examples can be added without rewriting the whole story.

## Deliverable Sources

- Evidence source of truth: `docs/final_deliverable_evidence_table.md`
- Presentation plan: `docs/presentation_roadmap_12min.md`
- ACL-style report plan: `docs/acl_report_outline.md`
- Excluded example appendix source: `docs/excluded_examples_summary.md`
- Q&A preparation: `docs/professor_qna_prep.md`
- Detailed pilot comparison: `docs/two_example_pilot_comparison.md`

## Core Narrative

1. The project studies whether a minimal prompt correction can move a model from a reproduced hallucination to a verified-truth answer.
2. Validated clean/corrupted pairs give a controlled intervention setup for mechanistic tracing.
3. The current pilot traces two examples, `369` and `813`, through validation, forward-pass alignment, layer patching, head patching, and head ablation.
4. Both examples show their strongest repeated signal at the layer level in late layers around `L29-L30`.
5. Exact head candidates differ, so the current evidence should be framed as pilot evidence and a hypothesis generator.

## Update Workflow for New Examples

When a new example completes validation and tracing:

1. Add a new row to `docs/final_deliverable_evidence_table.md`.
2. Add or update an example-specific findings file under `docs/`.
3. Add an example subsection to the ACL Results outline.
4. Update the cross-example comparison table only if the new result changes the pattern or adds a meaningful contrast.
5. Update presentation slides only if the new example changes the high-level story; otherwise keep detailed numbers in backup/Q&A.
6. Add failed or parked examples to `docs/excluded_examples_summary.md` rather than hiding them.

## Recommended Claim Boundaries

Allowed:

- Late-layer causal restoration appears in two pilot examples.
- Both completed examples implicate late layers around `L29-L30`.
- The exact head candidates differ across examples.
- The workflow is feasible for adding more validated examples.

Not allowed:

- A stable hallucination circuit has been discovered.
- A specific head or head family explains this hallucination class.
- Results generalize beyond `llama-2-7b-chat`.
- Results generalize beyond the two completed examples.

## Presentation vs. Report Emphasis

The presentation should focus on motivation, setup, method, the two-example pattern, and limitations. It should avoid dense artifact details except in backup slides.

The ACL-style report should include the full modular structure: dataset scope, registry/run workflow, validation criteria, patching method, per-example results, cross-example comparison, limitations, and appendices.
