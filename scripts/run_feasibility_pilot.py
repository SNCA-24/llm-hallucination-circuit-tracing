import sys
import os
import json
import traceback
from pathlib import Path

# Fix path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.config import load_config
from src.data.loaders import RAGTruthLoader
from src.filtering.pilot_number_subset import NumericDateFeasibilityFilter

def run():
    config_path = os.path.join("configs", "feasibility_pilot.yaml")
    
    audit_data = {
        "config": {},
        "repo_discovery": {},
        "schema_observations": {},
        "record_loading": {},
        "filtering": {},
        "blockers": [],
        "errors": []
    }

    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config not found at {config_path}")

        config = load_config(config_path)
        audit_data["config"] = {
            "primary_model": config.primary_model,
            "hallucination_type": config.hallucination_type,
            "pilot_sample_size": config.pilot_sample_size
        }
        print(f"Loaded config: {config.hallucination_type} pilot for {config.primary_model}")

        loader = RAGTruthLoader(config.ragtruth_xtended_repo_path, config.primary_dataset)
        
        # 1. Inspect Schema & Discovery
        print("\nInspecting repository schema...")
        try:
            schema_info = loader.inspect_schema(config.primary_model)
            audit_data["repo_discovery"]["discovered_files"] = schema_info.get("discovered_files", [])
            audit_data["repo_discovery"]["chosen_file"] = schema_info.get("chosen_file", None)
            
            audit_data["schema_observations"]["top_level_type"] = schema_info.get("top_level_type", "unknown")
            audit_data["schema_observations"]["approx_sample_count"] = schema_info.get("approx_sample_count", 0)
            audit_data["schema_observations"]["example_keys"] = schema_info.get("example_keys", [])
            
            if "schema_error" in schema_info:
                audit_data["blockers"].append(f"Schema inspection error: {schema_info['schema_error']}")
                
            print(f"Chosen file: {audit_data['repo_discovery']['chosen_file']}")
            print(f"Schema type: {audit_data['schema_observations']['top_level_type']} with ~{audit_data['schema_observations']['approx_sample_count']} samples.")
        except Exception as e:
            audit_data["errors"].append(f"Discovery error: {traceback.format_exc()}")
            print(f"Discovery error: {e}")
            raise e # Cannot continue without files

        # 2. Load candidates
        print("Loading records...")
        records = []
        try:
            for idx, rec in enumerate(loader.iter_records(config.primary_model)):
                records.append(rec)
                if idx >= 1000:
                    break
            audit_data["record_loading"]["scanned_records"] = len(records)
            print(f"Loaded {len(records)} records for inspection.")
        except Exception as e:
            audit_data["errors"].append(f"Record loading error: {traceback.format_exc()}")
            print(f"Record loading error: {e}")

        # 3. Filter suitable pilots
        pilot_set = []
        try:
            filt = NumericDateFeasibilityFilter(max_span_length=50)
            candidates, rejections = filt.filter_records(records)
            
            pilot_set = candidates[:config.pilot_sample_size]
            audit_data["filtering"] = {
                "candidates_found": len(candidates),
                "pilot_set_size": len(pilot_set),
                "rejections": rejections
            }
            print(f"Found {len(candidates)} candidates. Selected {len(pilot_set)} pilot candidate examples.")
        except Exception as e:
            audit_data["errors"].append(f"Filtering error: {traceback.format_exc()}")
            print(f"Filtering error: {e}")

        # 4. Save previews
        if pilot_set:
            try:
                output_path = config.output_paths["curated_examples"]
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    for p in pilot_set:
                        f.write(json.dumps(p) + '\n')
                print(f"Saved pilot candidate examples to {output_path}")
            except Exception as e:
                audit_data["errors"].append(f"Output save error: {traceback.format_exc()}")
                print(f"Output save error: {e}")

    except Exception as e:
        print(f"Fatal error during execution: {e}")
        audit_data["errors"].append(f"Fatal error: {traceback.format_exc()}")
    
    finally:
        # 5. Always write Audit Document
        audit_path = config.output_paths["audit_docs"] if "config" in locals() and hasattr(config, "output_paths") else "docs/dataset_feasibility_audit.md"
        Path(audit_path).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(audit_path, 'w') as f:
                f.write("# Phase 0 Dataset Feasibility Audit\n\n")
                
                f.write("## 1. Config Summary\n")
                f.write(f"- Primary Model: {audit_data['config'].get('primary_model', 'N/A')}\n")
                f.write(f"- Hallucination Target: {audit_data['config'].get('hallucination_type', 'N/A')}\n\n")
                
                f.write("## 2. Repo Discovery Summary\n")
                f.write("- Discovered Files:\n")
                for df in audit_data['repo_discovery'].get("discovered_files", []):
                    f.write(f"  - {df}\n")
                f.write(f"- Chosen File: {audit_data['repo_discovery'].get('chosen_file', 'None')}\n\n")
                
                f.write("## 3. Schema Observations\n")
                f.write(f"- Top Level Type: {audit_data['schema_observations'].get('top_level_type', 'N/A')}\n")
                f.write(f"- Approx Sample Count: {audit_data['schema_observations'].get('approx_sample_count', 0)}\n")
                f.write(f"- Example Keys: {', '.join(audit_data['schema_observations'].get('example_keys', []))}\n\n")
                f.write("> **Note:** We do not assume `source_info` is the final prompt string. We preserve raw fields and map them to `_candidate` suffixes.\n\n")
                
                f.write("## 4. Record Loading Summary\n")
                f.write(f"- Scanned Records: {audit_data['record_loading'].get('scanned_records', 0)}\n\n")
                
                f.write("## 5. Candidate Filtering Summary\n")
                f.write(f"- Heuristic Candidates Found: {audit_data['filtering'].get('candidates_found', 0)}\n")
                f.write(f"- Pilot Set Size: {audit_data['filtering'].get('pilot_set_size', 0)}\n")
                f.write("- Rejections Breakdown:\n")
                for reason, count in audit_data['filtering'].get('rejections', {}).items():
                    f.write(f"  - {reason}: {count}\n")
                f.write("\n")
                
                f.write("## 6. Blockers / Uncertainties\n")
                if not audit_data["blockers"]:
                    f.write("- No immediate structural blockers detected.\n")
                else:
                    for b in audit_data["blockers"]:
                        f.write(f"- {b}\n")
                f.write("- Schema Uncertainty: The base dataset does not label 'number hallucination' natively. We use a conservative regex to find digits within short spans.\n")
                f.write("- Prompt Fields Uncertainty: We have mapped potential inputs to `prompt_candidate` but exact templating format is unverified.\n\n")
                
                f.write("## 7. Errors Encountered\n")
                if not audit_data["errors"]:
                    f.write("- None.\n\n")
                else:
                    for e in audit_data["errors"]:
                        f.write(f"```text\n{e}\n```\n")
                
                f.write("## 8. Next Recommended Action\n")
                if audit_data["errors"] or not audit_data['filtering'].get('candidates_found', 0):
                    f.write("- **Action Required**: Inspect execution errors or zero-yield filters. Adjust heuristics or dataset references based on the schema.\n")
                else:
                    f.write("- **Proceed to Phase 1/2**: Build minimal-edit pairs (clean vs corrupted) for the exported pilot candidate examples.\n")
                    
            print(f"\nSaved structured audit doc to {audit_path}")
        except Exception as e:
            print(f"Failed to save audit document: {e}")

if __name__ == "__main__":
    run()
