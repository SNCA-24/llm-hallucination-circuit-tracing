# Next Candidate Triage

## Scope
- This shortlist is for the next manual-review round only.
- It is derived from the existing short single-span candidate pool in the `llama-2-7b-chat` RAGTruth_Xtended slice, plus the prior token-span feasibility notes for the 10-example pilot.
- Ranking follows the current guidance: prefer `date/year`, then `number/count`, then short `entity/title` completions.

## Shortlisted 20

| Rank | Example ID | Category | Token Mapping | Why Shortlisted |
| --- | --- | --- | --- | --- |
| 1 | `93` | date/year | already clean | Single unsupported year token with the cleanest existing token-map signal. |
| 2 | `2265` | date/year | needs checking | Compact month-year addition; likely easy to verify and edit minimally. |
| 3 | `2781` | date/year | needs checking | Specific year is injected into an otherwise grounded detention timeline. |
| 4 | `3573` | date/year | needs checking | Full calendar date appears invented and should trace as a short temporal span. |
| 5 | `2793` | date/year | needs checking | Standalone future year insertion is compact and likely lexical rather than punctuation-led. |
| 6 | `75` | date/year | needs checking | Premiere date is clearly unsupported; only risk is the previously ambiguous token boundary. |
| 7 | `4563` | date/year | needs checking | `since 2019` is a strong temporal anchor that should admit a small corrective edit. |
| 8 | `4365` | date/year | needs checking | Exact start date looks invented and highly localizable. |
| 9 | `2199` | date/year | needs checking | Anniversary count is short, concrete, and likely correctable with a small rewrite. |
| 10 | `2073` | date/year | needs checking | Added December release timing is concise and may validate cleanly. |
| 11 | `597` | number/count | already clean | Short duration claim with already-clean token mapping makes it an efficient reuse candidate. |
| 12 | `813` | number/count | needs checking | Strong numeric contradiction `10` versus the source-supported count. |
| 13 | `1407` | number/count | needs checking | `49 days` looks like a crisp numeric/time mismatch with a minimal fix path. |
| 14 | `2841` | number/count | needs checking | Unsupported dollar amount is specific and localized. |
| 15 | `3381` | number/count | needs checking | Per-item price claim should yield a lexical monetary divergence, not a punctuation-only one. |
| 16 | `3321` | number/count | needs checking | `34 states` versus `34 deaths` is a strong semantic-number swap with clear interpretability value. |
| 17 | `2439` | number/count | needs checking | Compact age token and likely tractable, but the source truth appears ambiguous `54 or 55`, so it is not top-tier. |
| 18 | `3411` | date/year | needs checking | Historical count plus `last year` phrasing is promising if the year can be verified tightly. |
| 19 | `513` | entity/title | needs checking | Short named-entity completion is a reasonable lexical backup if we need one non-numeric case. |
| 20 | `951` | entity/title | needs checking | Named entity plus apology action is compact and probably minimally editable. |

## Checked IDs
- `2439`: valid review candidate and shortlisted, but not top priority because the source appears to support `54 or 55`, which weakens truth crispness.
- `513`: valid low-priority backup candidate and shortlisted as an entity/title-style lexical completion.
- `573`: checked but not shortlisted. It looks more like a broader event-frame paraphrase (`during a training exercise`) than a clean date/number or short entity/title completion, so it is less practical for the next replication round.

## Ranking Rationale
- Ranks `1-10` favor explicit unsupported dates or years because they are most likely to give compact lexical divergences with minimal prompt edits.
- Ranks `11-18` are number/count cases that still look local and interpretable, but a few carry extra risk from ambiguity or semantic-role drift.
- Ranks `19-20` are backup entity/action completions kept in reserve in case the next round needs one short non-numeric example.

## Recommended First Review Batch
- `93`
- `2265`
- `2781`
- `3573`
- `813`

These five are the best balance of compact divergence, likely lexical signal, and practical minimal-edit feasibility. If you want a sixth backup immediately behind them, use `2793`.
