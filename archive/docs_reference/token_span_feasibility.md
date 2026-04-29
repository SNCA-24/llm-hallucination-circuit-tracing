# Token Span Feasibility Check

- **Tokenizer**: `NousResearch/Llama-2-7b-chat-hf` (Llama-2-7b equivalent)
- **Total Examples Checked**: 10
- **Clean Mappings**: 4
- **Ambiguous Mappings**: 6
- **Failed Mappings**: 0

## Diagnostics Summary
> **Clean** means the reported character span maps directly to whole token boundaries.
> **Ambiguous** means the character span cuts through the middle of a tokenizer subword, requiring a split-token patching strategy eventually.

## Per-Example Notes

### Example 51
- Status: **SUCCESS**
- Mapping: **Clean**
- Target Substring (from Dataset labels): `On November 1, 2020,`
- Hallucinated Tokens extracted: `['▁On', '▁November', '▁', '1', ',', '▁', '2', '0', '2', '0', ',']`
- Token Indices: `[0, 10]`
- First hallucinated token index: `0`
- Notes:
  - Clean mapping.

### Example 75
- Status: **SUCCESS**
- Mapping: **Ambiguous**
- Target Substring (from Dataset labels): `premieres on April 1st,`
- Hallucinated Tokens extracted: `['▁premier', 'es', '▁on', '▁April', '▁', '1', 'st', ',']`
- Token Indices: `[12, 19]`
- First hallucinated token index: `12`
- Notes:
  - Start boundary cuts through token '▁premier'. Char start: 52, Token start: 51.

### Example 93
- Status: **SUCCESS**
- Mapping: **Clean**
- Target Substring (from Dataset labels): `2012`
- Hallucinated Tokens extracted: `['2', '0', '1', '2']`
- Token Indices: `[116, 119]`
- First hallucinated token index: `116`
- Notes:
  - Clean mapping.

### Example 111
- Status: **SUCCESS**
- Mapping: **Ambiguous**
- Target Substring (from Dataset labels): `the song has endured for over 40 years`
- Hallucinated Tokens extracted: `['▁the', '▁song', '▁has', '▁end', 'ured', '▁for', '▁over', '▁', '4', '0', '▁years']`
- Token Indices: `[86, 96]`
- First hallucinated token index: `86`
- Notes:
  - Start boundary cuts through token '▁the'. Char start: 269, Token start: 268.

### Example 237
- Status: **SUCCESS**
- Mapping: **Ambiguous**
- Target Substring (from Dataset labels): `found by a passerby on Friday, April 9th`
- Hallucinated Tokens extracted: `['▁found', '▁by', '▁a', '▁passer', 'by', '▁on', '▁Friday', ',', '▁April', '▁', '9', 'th']`
- Token Indices: `[121, 132]`
- First hallucinated token index: `121`
- Notes:
  - Start boundary cuts through token '▁found'. Char start: 526, Token start: 525.

### Example 327
- Status: **SUCCESS**
- Mapping: **Ambiguous**
- Target Substring (from Dataset labels): `Of the 81 vaccinated individuals`
- Hallucinated Tokens extracted: `['▁Of', '▁the', '▁', '8', '1', '▁v', 'acc', 'in', 'ated', '▁individuals']`
- Token Indices: `[69, 78]`
- First hallucinated token index: `69`
- Notes:
  - Start boundary cuts through token '▁Of'. Char start: 304, Token start: 303.

### Example 369
- Status: **SUCCESS**
- Mapping: **Clean**
- Target Substring (from Dataset labels): `1986 John Hughes film "Pretty in Pink"`
- Hallucinated Tokens extracted: `['1', '9', '8', '6', '▁John', '▁Hugh', 'es', '▁film', '▁"', 'Pre', 'tty', '▁in', '▁P', 'ink', '"']`
- Token Indices: `[13, 27]`
- First hallucinated token index: `13`
- Notes:
  - Clean mapping.

### Example 423
- Status: **SUCCESS**
- Mapping: **Ambiguous**
- Target Substring (from Dataset labels): `deaths of over 800 people`
- Hallucinated Tokens extracted: `['▁death', 's', '▁of', '▁over', '▁', '8', '0', '0', '▁people']`
- Token Indices: `[150, 158]`
- First hallucinated token index: `150`
- Notes:
  - Start boundary cuts through token '▁death'. Char start: 617, Token start: 616.

### Example 489
- Status: **SUCCESS**
- Mapping: **Ambiguous**
- Target Substring (from Dataset labels): `accumulating over 200 credits to his name`
- Hallucinated Tokens extracted: `['▁accum', 'ulating', '▁over', '▁', '2', '0', '0', '▁cred', 'its', '▁to', '▁his', '▁name']`
- Token Indices: `[133, 144]`
- First hallucinated token index: `133`
- Notes:
  - Start boundary cuts through token '▁accum'. Char start: 511, Token start: 510.

### Example 597
- Status: **SUCCESS**
- Mapping: **Clean**
- Target Substring (from Dataset labels): `30 years after the original.`
- Hallucinated Tokens extracted: `['3', '0', '▁years', '▁after', '▁the', '▁original', '.']`
- Token Indices: `[32, 38]`
- First hallucinated token index: `32`
- Notes:
  - Clean mapping.

