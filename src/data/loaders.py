import json
import os
from pathlib import Path
from typing import Iterator, Dict, Any, List, Tuple

class RAGTruthLoader:
    """Read-only loader for RAGTruth / RAGTruth_Xtended datasets."""
    
    def __init__(self, repo_path: str, dataset_name: str):
        self.repo_path = Path(repo_path)
        self.dataset_name = dataset_name # e.g. "ragtruth_xtended"
        
    def discover_model_file(self, model_name: str) -> Path:
        """Find the relevant JSON/JSONL file for the given model without assuming exact naming."""
        search_dirs = [
            self.repo_path / "dataset" / "rtx" / model_name,
            self.repo_path / "dataset" / model_name,
            self.repo_path / "data" / model_name
        ]
        
        for d in search_dirs:
            if d.exists() and d.is_dir():
                for file_path in d.glob("*.json"):
                    if file_path.is_file():
                        return file_path
                for file_path in d.glob("*.jsonl"):
                    if file_path.is_file():
                        return file_path
                        
        raise FileNotFoundError(f"Could not discover data file for model {model_name} in {self.repo_path}")

    def inspect_schema(self, model_name: str) -> Dict[str, Any]:
        """
        Inspect discovery and schema without loading everything.
        Returns a summary dictionary of schema observations.
        """
        summary = {
            "discovered_files": [],
            "chosen_file": None,
            "top_level_type": "unknown",
            "approx_sample_count": 0,
            "example_keys": []
        }
        
        search_dirs = [
            self.repo_path / "dataset" / "rtx" / model_name,
            self.repo_path / "dataset" / model_name,
            self.repo_path / "data" / model_name
        ]
        
        candidates = []
        for d in search_dirs:
            if d.exists() and d.is_dir():
                for ext in ["*.json", "*.jsonl"]:
                    for f in d.glob(ext):
                        if f.is_file():
                            candidates.append(f)
                            summary["discovered_files"].append(str(f))
                            
        if not candidates:
            return summary
            
        chosen_file = candidates[0]
        summary["chosen_file"] = str(chosen_file)
        
        if chosen_file.suffix == '.json':
            with open(chosen_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        summary["top_level_type"] = "list"
                        summary["approx_sample_count"] = len(data)
                        if data:
                            summary["example_keys"] = list(data[0].keys())
                    elif isinstance(data, dict):
                        summary["top_level_type"] = "dict"
                        summary["approx_sample_count"] = len(data)
                        if data:
                            first_val = next(iter(data.values()))
                            if isinstance(first_val, dict):
                                summary["example_keys"] = list(first_val.keys())
                            else:
                                summary["example_keys"] = []
                except Exception as e:
                    summary["schema_error"] = str(e)
                    
        elif chosen_file.suffix == '.jsonl':
            summary["top_level_type"] = "jsonl (list of dicts)"
            count = 0
            with open(chosen_file, 'r', encoding='utf-8') as f:
                for idx, line in enumerate(f):
                    count += 1
                    if idx == 0:
                        try:
                            record = json.loads(line)
                            summary["example_keys"] = list(record.keys())
                        except:
                            pass
            summary["approx_sample_count"] = count
            
        return summary

    def iter_records(self, model_name: str) -> Iterator[Dict[str, Any]]:
        """Yield normalized lightweight records for pilot exploration."""
        file_path = self.discover_model_file(model_name)
        
        def _normalize(idx, record):
            # SCHEMA UNCERTAINTY: We do not assume source_info is the final prompt.
            # We expose candidates but preserve raw fields.
            return {
                "example_id": record.get("id", str(idx)),
                "prompt_candidate": record.get("source_info", record.get("prompt", "")), 
                "response_candidate": record.get("response", ""),
                "labels_candidate": record.get("labels", []),
                "source": record.get("source", ""),
                "raw": record
            }
        
        if file_path.suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for idx, record in enumerate(data):
                        yield _normalize(idx, record)
                elif isinstance(data, dict):
                    # Interpret dict-of-dicts dataset format
                    for idx, (key, val) in enumerate(data.items()):
                        if isinstance(val, dict):
                            val_copy = dict(val)
                            if "id" not in val_copy:
                                val_copy["id"] = key
                            yield _normalize(idx, val_copy)
                        else:
                            yield _normalize(idx, {"value": val, "id": key})
                            
        elif file_path.suffix == '.jsonl':
            with open(file_path, 'r', encoding='utf-8') as f:
                for idx, line in enumerate(f):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    yield _normalize(idx, record)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
