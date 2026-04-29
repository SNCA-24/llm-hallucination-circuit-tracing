# Next-Round Token Span Feasibility

- **Tokenizer**: `NousResearch/Llama-2-7b-chat-hf` (Llama-2-7b equivalent)
- **Total Examples Checked**: 5
- **Clean Mappings**: 3
- **Ambiguous Mappings**: 2
- **Failed Mappings**: 0

## Summary
> **Clean** means the reported character span maps directly to whole token boundaries.
> **Ambiguous** means the character span overlaps tokens but cuts through at least one token boundary.
> **Failed** means the reported character span could not be aligned to overlapping tokens.

## Per-Example Notes

### Example 2265
- Status: **AMBIGUOUS**
- Hallucinated Substring: `April 2019`
- Hallucinated Char Span: `[166, 176]`
- Token Span: `[52, 57]`
- First hallucinated token index: `52`
- Hallucinated Tokens extracted: `['▁April', '▁', '2', '0', '1', '9']`
- Notes:
  - Start boundary cuts through token '▁April'. Char start: 166, Token start: 165.

### Example 2781
- Status: **AMBIGUOUS**
- Hallucinated Substring: `Gao was detained in April 2013`
- Hallucinated Char Span: `[312, 342]`
- Token Span: `[68, 79]`
- First hallucinated token index: `68`
- Hallucinated Tokens extracted: `['▁G', 'ao', '▁was', '▁det', 'ained', '▁in', '▁April', '▁', '2', '0', '1', '3']`
- Notes:
  - Start boundary cuts through token '▁G'. Char start: 312, Token start: 311.

### Example 3573
- Status: **CLEAN**
- Hallucinated Substring: `On Saturday, April 10`
- Hallucinated Char Span: `[0, 21]`
- Token Span: `[0, 6]`
- First hallucinated token index: `0`
- Hallucinated Tokens extracted: `['▁On', '▁Saturday', ',', '▁April', '▁', '1', '0']`
- Notes:
  - Clean mapping.

### Example 2793
- Status: **CLEAN**
- Hallucinated Substring: `2020`
- Hallucinated Char Span: `[360, 364]`
- Token Span: `[83, 86]`
- First hallucinated token index: `83`
- Hallucinated Tokens extracted: `['2', '0', '2', '0']`
- Notes:
  - Clean mapping.

### Example 813
- Status: **CLEAN**
- Hallucinated Substring: `10 counts of fraud`
- Hallucinated Char Span: `[52, 70]`
- Token Span: `[17, 22]`
- First hallucinated token index: `17`
- Hallucinated Tokens extracted: `['1', '0', '▁counts', '▁of', '▁fra', 'ud']`
- Notes:
  - Clean mapping.

## Recommendation
- Move these next to manual review: `2265, 3573, 2793`
- Prioritize clean mappings first. Among the clean cases, prefer compact lexical date/year divergences over broader semantic spans.

## Canonical Registry Note
- Future token-span and validation scripts should update and read `outputs/examples_registry.csv`.
- `outputs/next_round_token_span_feasibility.jsonl` remains as an archived run artifact.
