import sys
import os
import json
import csv
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.pairs.pair_construction_pilot import PairConstructionScaffold

def run():
    curated_file = "outputs/pilot_curated_examples.jsonl"
    token_file = "outputs/token_span_feasibility.jsonl"
    jsonl_output_file = "outputs/pair_construction_candidates.jsonl"
    csv_output_file = "outputs/pair_authoring_review_sheet.csv"
    audit_file = "docs/pair_construction_pilot.md"
    
    if not (os.path.exists(curated_file) and os.path.exists(token_file)):
        print(f"Error: Required prior outputs missing. Ensure {curated_file} and {token_file} exist.")
        return

    # Load curated
    curated_data = {}
    with open(curated_file, 'r') as f:
        for line in f:
            if not line.strip(): continue
            rec = json.loads(line)
            curated_data[rec["example_id"]] = rec
            
    # Load token feasibility
    token_data = {}
    with open(token_file, 'r') as f:
        for line in f:
            if not line.strip(): continue
            rec = json.loads(line)
            token_data[rec["example_id"]] = rec

    allowed_edits = [
        "short_disambiguating_clause",
        "one_added_supporting_evidence_sentence",
        "small_clarification_phrase",
        "format_preserving_rewrite"
    ]
    scaffold = PairConstructionScaffold(allowed_edit_classes=allowed_edits)
    
    target_ids = {"51", "93", "369", "597"}
    
    clean_candidates = []
    for eid in target_ids:
        tok_info = token_data.get(eid)
        if not tok_info:
            print(f"Warning: Target ID {eid} not found in token mapping results.")
            continue
            
        curated_ex = curated_data.get(eid)
        if curated_ex:
            candidate = scaffold.build_candidate_record(curated_ex, tok_info)
            clean_candidates.append(candidate)
                
    if not clean_candidates:
        print("Warning: No exact targets mapped to scaffold successfully.")
        return

    # Save JSONL fallback
    Path(jsonl_output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(jsonl_output_file, 'w') as f:
        for c in clean_candidates:
            f.write(json.dumps(c) + '\n')
            
    # Save CSV for manual spreadsheet review
    Path(csv_output_file).parent.mkdir(parents=True, exist_ok=True)
    if clean_candidates:
        fields = list(clean_candidates[0].keys())
        with open(csv_output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for c in clean_candidates:
                # Map None gracefully to empty strings for editors
                writer.writerow({k: (v if v is not None else "") for k, v in c.items()})

    # Generate the Markdown doc
    Path(audit_file).parent.mkdir(parents=True, exist_ok=True)
    with open(audit_file, 'w') as f:
        f.write("# Pair Construction Pilot & Truth Recovery\n\n")
        f.write("## Overview\n")
        f.write(f"This document prepares the {len(clean_candidates)} strictly selected examples ({', '.join(target_ids)}) for human-in-the-loop manual truth recovery and pair authoring.\n")
        f.write("These examples were retained based on flawless character->token spans. We are explicitly decoupling truth-extraction from prompt-formatting to remain conservative.\n\n")
        
        f.write("## Important Semantic Field Changes\n")
        f.write("- **Prompt vs Context**: We previously used a collapsed `original_prompt` field. We have corrected this semantic export bug.\n")
        f.write("- **Clean Prompt**: The field `clean_input_text_for_validation` is mapped directly from the dataset's raw `prompt` field. This is the actual instruction passed to the LLM.\n")
        f.write("- **Context/Evidence**: The field `supporting_context_excerpt` is strictly sourced from `source_info`, which houses the document base.\n")
        f.write("- **Fallback Policy**: Our scaffold dictates that if `prompt` is empty, it relies on `source_info` as the clean input, adding an explicit warning flag.\n\n")
        
        f.write("## Retained Clean Examples\n\n")
        for c in clean_candidates:
            eid = c.get("example_id")
            hallucination = c.get("hallucinated_substring")
            raw_gt = c.get("raw_ground_truth_field")
            
            f.write(f"### Example {eid}\n")
            f.write(f"- **Task Type**: `{c.get('task_type')}`\n")
            f.write(f"- **Hallucinated Substring**: `{hallucination}`\n")
            f.write(f"- **Raw Dataset Metadata**: `{raw_gt}`\n")
            if c.get("prompt_fallback_warning"):
                 f.write(f"- **WARNING**: {c.get('prompt_fallback_warning')}\n")
            f.write("- **Truth Recovery Needs**: Review the `supporting_context_excerpt` within the generated CSV and extract the actual historical or factual answer. Populate it manually into `ground_truth_text_verified`.\n\n")
            
        f.write("## Allowed Edit Classes\n")
        f.write("When configuring `corrupted_prompt_candidate` inside the CSV, utilize exactly one of the mapped PRD classes:\n")
        for cls in allowed_edits:
            f.write(f"- `{cls}`\n")
            
        f.write("\n## Next Steps (Human Annotation Workflow)\n")
        f.write("1. **Verify ground truth manually**: Open `outputs/pair_authoring_review_sheet.csv`. Extract the factual target from the dataset context excerpt and commit it to the `ground_truth_text_verified` column.\n")
        f.write("2. **Draft corrupted prompts**: Using that verified truth, construct a minimal-edit correction and insert it into `corrupted_prompt_candidate`. Ensure you fill out the `edit_class` and `edit_delta_text` flags.\n")
        f.write("3. **Suspend Validation**: Do NOT execute model generators. Await explicit Phase 3 framework deployment to run the structural `clean_reproduction_status` and `corrupted_flip_status` sequences over this CSV.\n")
        
    print(f"\nGenerated Truth Recovery scaffolds for examples: {', '.join(target_ids)}")
    print(f"Spreadsheet Export: {csv_output_file}")
    print(f"Audit Status: {audit_file}\n")

if __name__ == "__main__":
    run()
