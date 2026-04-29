# Pair Validation

Historical note: this document records run-1 results. Future validation scripts should read and update `outputs/examples_registry.csv` rather than creating a new bespoke review sheet.

## Scope
- Input CSV: `outputs/pair_authoring_review_sheet.csv`
- Allowed example IDs: `51`, `369`
- Model scope: `llama-2-7b-chat` only
- Phase boundary: pair validation only; no tracing implemented here

## Generation Settings
- `max_new_tokens`: `96`
- `do_sample`: `False`
- `temperature`: `0.0`
- `top_p`: `1.0`
- `repetition_penalty`: `1.0`
- `seed`: `42`

## Input Filtering
- Eligible rows run: 2
- Eligible rows skipped: 0

## Per-Example Results
### Example 51
- Clean reproduction status: `not_reproduced`
- Corrupted flip status: `truth_present_but_hallucination_still_present`
- Verified truth appears in corrupted output: `True`
- Clean output contains hallucinated substring: `False`
- Corrupted output contains hallucinated substring: `True`
- Clean output: `In November 2014, Hong Kong police found two dead bodies in an apartment in Wan Chai, an inner-city suburb. The victims were identified as 29-year-old Seneng Mujiasih and 25-year-old Sumarti Ningsih, both domestic workers from Indonesia. The suspect, 29-year-old Rurik Jutting, a former banker,`
- Corrupted output: `On November 1, 2020, Hong Kong police found two dead bodies in an apartment in Wan Chai, an inner-city suburb. The victims were identified as 29-year-old Seneng Mujiasih and 25-year-old Sumarti Ningsih. The former banker, Rurik Jutting, was charged with two counts of murder. The victims were domestic workers`

### Example 369
- Clean reproduction status: `reproduced_hallucination`
- Corrupted flip status: `flipped_to_verified_truth`
- Verified truth appears in corrupted output: `True`
- Clean output contains hallucinated substring: `True`
- Corrupted output contains hallucinated substring: `False`
- Clean output: `Jon Cryer reprised his iconic dance routine from the 1986 John Hughes film "Pretty in Pink" on "The Late Late Show" with James Corden, who fulfilled a childhood dream.`
- Corrupted output: `Jon Cryer reprised his iconic dance routine from the 1986 John Hughes film, complete with white shoes and wall-dancing, on James Corden's "Late Late Show." Cryer, now 50, danced in tandem with Corden, who fulfilled a childhood dream by recreating the scene. The original fans, many now in middle age, may have squealed with delight at the repr`
