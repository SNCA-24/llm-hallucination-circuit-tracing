# Excluded Examples Summary

This appendix-style table summarizes known failed, parked, or ambiguous examples. These examples should not be treated as completed tracing evidence.

| Example | Status | Reason | Revisit later? |
| --- | --- | --- | --- |
| `51` | Failed | Pair validation failed. The clean run did not provide a clean validated setup for tracing, and the corrupted prompt did not produce a sufficiently clean hallucination-to-truth flip for the pilot. | Low priority. Revisit only if prompt validation settings or reproduction criteria change. |
| `3573` | Failed | Pair validation failed. The clean run did not reproduce the target date hallucination, and the corrupted run did not flip cleanly to the intended day-only correction. | Low priority for current pilot. Revisit only if date-target prompt design is revised. |
| `93` | Parked | Earlier review parked it rather than moving it through the full validated tracing workflow. It involved a date/timeline correction target that remains unvalidated for tracing. | Possible later, after the current validated set is expanded. |
| `597` | Parked | Earlier review parked it rather than moving it through the full validated tracing workflow. It involved a release-timing correction target that remains unvalidated for tracing. | Possible later, after the current validated set is expanded. |
| `2793` | Parked | Correction target was weak, so the clean/corrupted contrast was not strong enough for a reliable tracing pilot. | Low priority unless a stronger verified correction target is found. |
| `2265` | Ambiguous | Token mapping was ambiguous, making the hallucinated span unsuitable for the current token-level tracing workflow. | Revisit only if the workflow adds a split-token or ambiguous-span policy. |
| `2781` | Ambiguous | Token mapping was ambiguous, making the hallucinated span unsuitable for the current token-level tracing workflow. | Revisit only if the workflow adds a split-token or ambiguous-span policy. |

These rows are useful for an appendix or backup slide because they show that examples were filtered by validation and token-mapping criteria rather than selected only after successful tracing.
