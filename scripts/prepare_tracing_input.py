import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.workflow.run_artifacts import (
    build_manifest,
    create_run_directory,
    read_jsonl,
    read_registry,
    short_scope_from_ids,
    summarize_run_status,
    utc_timestamp,
    write_json,
)


STAGE_NAME = "tracing_prep"
DEFAULT_REGISTRY = "outputs/examples_registry.csv"
DEFAULT_RUNS_ROOT = "outputs/runs"
REQUIRED_REGISTRY_FIELDS = [
    "example_id",
    "validated_pair_flag",
    "clean_reproduction_status",
    "corrupted_flip_status",
    "validation_results_path",
    "latest_artifact_root",
    "clean_input_text_for_validation",
    "corrupted_prompt_candidate",
    "ground_truth_text_verified",
    "hallucinated_substring",
    "hallucinated_char_span",
    "hallucinated_token_span",
    "first_hallucinated_token_index",
    "edit_class",
    "edit_delta_text",
    "why_minimal",
]
OUTPUT_FIELDS = [
    "example_id",
    "clean_input_text_for_validation",
    "corrupted_prompt_candidate",
    "built_clean_prompt",
    "built_corrupted_prompt",
    "ground_truth_text_verified",
    "hallucinated_substring",
    "hallucinated_char_span",
    "hallucinated_token_span",
    "first_hallucinated_token_index",
    "model_output_clean",
    "model_output_corrupted",
    "edit_class",
    "edit_delta_text",
    "why_minimal",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare run-scoped tracing input for one validated registry example.")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY, help="Canonical examples registry path.")
    parser.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT, help="Root directory for run-scoped artifacts.")
    parser.add_argument("--example-id", required=True, help="Validated example ID to export.")
    return parser.parse_args()


def truthy(value: Any) -> bool:
    return str(value or "").strip().casefold() in {"true", "t", "yes", "y", "1"}


def find_registry_row(registry_path: str, example_id: str) -> Dict[str, str]:
    rows, _fieldnames = read_registry(registry_path, extra_fields=REQUIRED_REGISTRY_FIELDS)
    matches = [row for row in rows if str(row.get("example_id", "")).strip() == str(example_id)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one registry row for example_id={example_id}, found {len(matches)}.")
    return matches[0]


def validate_registry_row(row: Dict[str, str]) -> List[str]:
    failures: List[str] = []
    if not truthy(row.get("validated_pair_flag")):
        failures.append("validated_pair_flag must be true")
    if str(row.get("clean_reproduction_status", "")).strip() != "reproduced_hallucination":
        failures.append("clean_reproduction_status must be reproduced_hallucination")
    if str(row.get("corrupted_flip_status", "")).strip() != "flipped_to_verified_truth":
        failures.append("corrupted_flip_status must be flipped_to_verified_truth")
    return failures


def candidate_validation_paths(row: Dict[str, str]) -> List[Path]:
    candidates: List[Path] = []
    registry_path = str(row.get("validation_results_path", "")).strip()
    if registry_path:
        candidates.append(Path(registry_path))

    artifact_root = str(row.get("latest_artifact_root", "")).strip()
    if artifact_root:
        root = Path(artifact_root)
        candidates.append(root / "pair_validation_results.jsonl")
        candidates.extend(sorted(root.glob("pair_validation_results*.jsonl")))
        candidates.extend(sorted(root.glob("*pair_validation*.jsonl")))

        for summary_name in ("summary.json", f"summary_{row.get('example_id')}.json"):
            summary_path = root / summary_name
            if not summary_path.exists():
                continue
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            artifact_path = summary.get("artifact_paths", {}).get("results_jsonl")
            if artifact_path:
                candidates.append(Path(artifact_path))
            for item in summary.get("processed_success", []):
                if isinstance(item, dict) and item.get("artifact_path"):
                    candidates.append(Path(item["artifact_path"]))

    deduped: List[Path] = []
    seen = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            deduped.append(candidate)
    return deduped


def load_validation_result(row: Dict[str, str]) -> tuple[Dict[str, Any], str]:
    example_id = str(row.get("example_id", "")).strip()
    attempted = []
    for candidate in candidate_validation_paths(row):
        attempted.append(str(candidate))
        if not candidate.exists():
            continue
        for record in read_jsonl(candidate):
            if str(record.get("example_id", "")).strip() != example_id:
                continue
            if record.get("status") == "success" and record.get("validation_gate_passed", True):
                return record, str(candidate)
    raise FileNotFoundError(
        "No successful pair-validation JSONL record found for "
        f"example_id={example_id}. Attempted: {attempted}"
    )


def build_tracing_payload(row: Dict[str, str], validation_result: Dict[str, Any]) -> Dict[str, Any]:
    merged = {
        "example_id": str(row.get("example_id", "")).strip(),
        "clean_input_text_for_validation": row.get("clean_input_text_for_validation", ""),
        "corrupted_prompt_candidate": row.get("corrupted_prompt_candidate", ""),
        "built_clean_prompt": validation_result.get("built_clean_prompt", ""),
        "built_corrupted_prompt": validation_result.get("built_corrupted_prompt", ""),
        "ground_truth_text_verified": row.get("ground_truth_text_verified", ""),
        "hallucinated_substring": row.get("hallucinated_substring", ""),
        "hallucinated_char_span": row.get("hallucinated_char_span", ""),
        "hallucinated_token_span": row.get("hallucinated_token_span", ""),
        "first_hallucinated_token_index": row.get("first_hallucinated_token_index", ""),
        "model_output_clean": validation_result.get("model_output_clean", ""),
        "model_output_corrupted": validation_result.get("model_output_corrupted", ""),
        "edit_class": row.get("edit_class", ""),
        "edit_delta_text": row.get("edit_delta_text", ""),
        "why_minimal": row.get("why_minimal", ""),
    }
    return {field: merged[field] for field in OUTPUT_FIELDS}


def main() -> None:
    args = parse_args()
    example_id = str(args.example_id).strip()
    row = find_registry_row(args.registry, example_id)
    failures = validate_registry_row(row)
    processed_success: List[Dict[str, Any]] = []
    processed_failed: List[Dict[str, Any]] = []
    skipped_ineligible: List[Dict[str, Any]] = []

    run_id, run_dir = create_run_directory(
        args.runs_root,
        STAGE_NAME,
        short_scope_from_ids([example_id]),
    )
    output_path = run_dir / "tracing_pilot_input.json"
    artifact_paths = {"tracing_pilot_input": str(output_path)}
    started_at = utc_timestamp()
    manifest = build_manifest(
        run_id=run_id,
        stage_name=STAGE_NAME,
        started_at=started_at,
        status="running",
        input_registry_path=args.registry,
        target_example_ids=[example_id],
        code_entrypoint="scripts/prepare_tracing_input.py",
        artifact_paths=artifact_paths,
        notes=["Prepared tracing input only. Forward pass and patching stages were not run."],
        backward_compatibility_mode=False,
    )
    write_json(run_dir / "manifest.json", manifest)

    if failures:
        skipped_ineligible.append({"example_id": example_id, "reason": "; ".join(failures)})
    else:
        try:
            validation_result, validation_artifact_path = load_validation_result(row)
            payload = build_tracing_payload(row, validation_result)
            write_json(output_path, payload)
            artifact_paths["source_pair_validation_result"] = validation_artifact_path
            processed_success.append({"example_id": example_id, "artifact_path": str(output_path)})
        except Exception as exc:
            processed_failed.append({"example_id": example_id, "reason": str(exc)})

    status = summarize_run_status(processed_success, processed_failed, [], skipped_ineligible)
    finished_at = utc_timestamp()
    summary = {
        "run_id": run_id,
        "stage_name": STAGE_NAME,
        "status": status,
        "finished_at": finished_at,
        "artifact_paths": artifact_paths,
        "target_example_ids": [example_id],
        "retained_example_ids": [item["example_id"] for item in processed_success],
        "processed_success": processed_success,
        "processed_failed": processed_failed,
        "skipped_already_done": [],
        "skipped_ineligible": skipped_ineligible,
        "forward_pass_run": False,
        "patching_run": False,
    }
    write_json(run_dir / "summary.json", summary)
    manifest["status"] = status
    manifest["finished_at"] = finished_at
    manifest["artifact_paths"] = artifact_paths
    write_json(run_dir / "manifest.json", manifest)

    print(f"Run ID: {run_id}")
    print(f"Run status: {status}")
    print(f"Run directory: {run_dir}")
    print(f"Retained example IDs: {', '.join(summary['retained_example_ids']) or 'none'}")
    if processed_failed or skipped_ineligible:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
