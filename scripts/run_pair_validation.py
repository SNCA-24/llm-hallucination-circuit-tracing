import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.config import load_config
from src.replay.pair_validation import (
    LlamaPairValidator,
    PairValidationInput,
    load_pair_validation_inputs,
    load_pair_validation_inputs_from_registry_rows,
    validation_passed,
    write_validation_markdown,
)
from src.workflow.run_artifacts import (
    append_jsonl,
    build_manifest,
    compact_notes,
    create_run_directory,
    find_successful_artifact,
    load_failed_ids_from_run,
    parameter_hash,
    read_registry,
    select_registry_rows,
    short_scope_from_ids,
    summarize_run_status,
    update_registry_row,
    utc_timestamp,
    write_json,
    write_jsonl,
)


STAGE_NAME = "pair_validation"
DEFAULT_REGISTRY = "outputs/examples_registry.csv"
DEFAULT_RUNS_ROOT = "outputs/runs"
PAIR_REGISTRY_FIELDS = [
    "clean_reproduction_status",
    "corrupted_flip_status",
    "validated_pair_flag",
    "validation_notes",
    "validation_results_path",
    "validation_target_flag",
    "final_status",
    "keep_reason",
    "latest_run_id",
    "latest_artifact_root",
    "last_updated_stage",
    "latest_stage_status",
    "latest_stage_notes",
]
TERMINAL_FINAL_STATUSES = {"processed_reject", "pilot_complete"}
PARKED_FINAL_STATUSES = {"parked", "processed_reject", "pilot_complete"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run registry-backed pair validation.")
    parser.add_argument("--config", default="configs/feasibility_pilot.yaml", help="Path to the YAML config file.")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY, help="Canonical examples registry path.")
    parser.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT, help="Root directory for run-scoped artifacts.")
    parser.add_argument("--example-ids", nargs="+", default=None, help="Example IDs to process.")
    parser.add_argument("--where-final-status", default=None, help="Narrow selection to rows with this final_status.")
    parser.add_argument("--where-validation-target", default=None, help="Narrow selection to validation_target_flag true/false.")
    parser.add_argument(
        "--rerun-failed-from-run",
        default=None,
        help="Run only examples listed in processed_failed in a previous run summary.",
    )
    parser.add_argument("--force", action="store_true", help="Rerun terminal or previously completed examples.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run without writing artifacts or registry updates.")
    parser.add_argument("--input-csv", default=None, help="Backward-compatible pair-validation CSV input path.")
    parser.add_argument("--target-example-ids", nargs="+", default=None, help="Backward-compatible alias for --example-ids.")
    parser.add_argument("--output-jsonl", default=None, help="Backward-compatible duplicate results JSONL path.")
    parser.add_argument("--output-doc", default=None, help="Backward-compatible duplicate markdown summary path.")
    return parser.parse_args()


def resolve_previous_run_dir(runs_root: str, run_id_or_path: str) -> Path:
    candidate = Path(run_id_or_path)
    if candidate.exists():
        return candidate
    return Path(runs_root) / run_id_or_path


def pair_is_terminal(row: Dict[str, str]) -> bool:
    return (
        str(row.get("validated_pair_flag", "")).strip().casefold() == "true"
        or str(row.get("final_status", "")).strip() in TERMINAL_FINAL_STATUSES
    )


def validation_notes(result: Dict[str, Any], passed: bool) -> str:
    if passed:
        return "Validated pair: clean run reproduced hallucination and corrupted run flipped to verified truth."
    return (
        "Validation failed: "
        f"clean={result.get('clean_reproduction_status', 'unknown')}; "
        f"corrupted={result.get('corrupted_flip_status', 'unknown')}."
    )


def result_to_registry_updates(result: Dict[str, Any], run_id: str, run_dir: Path, results_path: Path) -> Dict[str, Any]:
    passed = validation_passed(result)
    notes = validation_notes(result, passed)
    keep_reason = "Validated clean/corrupted pair." if passed else notes
    return {
        "clean_reproduction_status": result.get("clean_reproduction_status", ""),
        "corrupted_flip_status": result.get("corrupted_flip_status", ""),
        "validation_target_flag": "false",
        "validated_pair_flag": "true" if passed else "false",
        "validation_notes": notes,
        "validation_results_path": str(results_path),
        "final_status": "validated" if passed else "processed_reject",
        "keep_reason": keep_reason,
        "latest_run_id": run_id,
        "latest_artifact_root": str(run_dir),
        "last_updated_stage": STAGE_NAME,
        "latest_stage_status": "success" if passed else "failed",
        "latest_stage_notes": notes,
    }


def failure_to_registry_updates(example_id: str, reason: str, run_id: str, run_dir: Path, results_path: Path) -> Dict[str, Any]:
    return {
        "validation_target_flag": "false",
        "validated_pair_flag": "false",
        "validation_notes": f"Validation failed before completion: {reason}",
        "validation_results_path": str(results_path),
        "final_status": "parked",
        "keep_reason": f"Validation attempt failed before completion: {reason}",
        "latest_run_id": run_id,
        "latest_artifact_root": str(run_dir),
        "last_updated_stage": STAGE_NAME,
        "latest_stage_status": "failed",
        "latest_stage_notes": reason,
    }


def collect_registry_inputs(
    *,
    registry_path: str,
    runs_root: str,
    example_ids: Optional[Sequence[str]],
    where_final_status: Optional[str],
    where_validation_target: Optional[str],
    force: bool,
    model_alias: str,
    params_hash: str,
) -> Tuple[List[PairValidationInput], Dict[str, Any]]:
    rows, _fieldnames = read_registry(registry_path, extra_fields=PAIR_REGISTRY_FIELDS)
    selection = select_registry_rows(
        rows,
        example_ids=example_ids,
        where_final_status=where_final_status,
        where_validation_target=where_validation_target,
    )
    summary_bits: Dict[str, Any] = {
        "target_example_ids": selection["target_example_ids"],
        "duplicate_example_ids": selection["duplicate_example_ids"],
        "missing_example_ids": selection["missing_example_ids"],
        "processed_success": [],
        "processed_failed": [],
        "skipped_already_done": [],
        "skipped_ineligible": [],
    }
    for example_id in selection["missing_example_ids"]:
        summary_bits["skipped_ineligible"].append({"example_id": example_id, "reason": "example_id not present in registry"})
    for example_id in selection["filtered_out_example_ids"]:
        summary_bits["skipped_ineligible"].append({"example_id": example_id, "reason": "filtered out by registry selection flags"})

    runnable_rows: List[Dict[str, str]] = []
    for row in selection["rows"]:
        example_id = str(row.get("example_id", "")).strip()
        if pair_is_terminal(row) and not force:
            summary_bits["skipped_already_done"].append({"example_id": example_id, "reason": "terminal pair-validation state"})
            continue
        if str(row.get("final_status", "")).strip() in PARKED_FINAL_STATUSES and not force:
            summary_bits["skipped_ineligible"].append({"example_id": example_id, "reason": "parked/rejected/final row requires --force"})
            continue
        prior_artifact = find_successful_artifact(
            runs_root,
            stage_name=STAGE_NAME,
            example_id=example_id,
            model_alias=model_alias,
            parameters_hash=params_hash,
        )
        if prior_artifact and not force:
            summary_bits["skipped_already_done"].append({"example_id": example_id, "reason": "matching prior successful artifact", "artifact_path": prior_artifact})
            continue
        runnable_rows.append(row)

    inputs, skipped_rows = load_pair_validation_inputs_from_registry_rows(
        runnable_rows,
        allowed_example_ids=[str(row.get("example_id", "")).strip() for row in runnable_rows],
    )
    for skipped in skipped_rows:
        summary_bits["skipped_ineligible"].append(skipped)
    return inputs, summary_bits


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    if config.primary_model != "llama-2-7b-chat":
        raise ValueError("Pair validation is currently locked to primary_model='llama-2-7b-chat'.")
    generation_settings = dict(config.generation_settings or {})
    if not generation_settings:
        raise ValueError("generation_settings are missing from the config.")

    explicit_ids = args.example_ids or args.target_example_ids
    if args.rerun_failed_from_run:
        failed_ids = load_failed_ids_from_run(resolve_previous_run_dir(args.runs_root, args.rerun_failed_from_run))
        if explicit_ids:
            explicit_set = {str(example_id) for example_id in explicit_ids}
            explicit_ids = [example_id for example_id in failed_ids if example_id in explicit_set]
        else:
            explicit_ids = failed_ids

    backward_compatibility_mode = bool(args.input_csv or args.target_example_ids or args.output_jsonl or args.output_doc)
    params = {
        "model_alias": config.primary_model,
        "generation_settings": generation_settings,
    }
    params_hash = parameter_hash(params)

    if args.input_csv:
        target_ids = explicit_ids or list(dict.fromkeys(dict(config.pair_validation or {}).get("target_example_ids", ["51", "369"])))
        inputs, skipped_rows = load_pair_validation_inputs(args.input_csv, target_ids)
        summary: Dict[str, Any] = {
            "target_example_ids": [str(example_id) for example_id in target_ids],
            "duplicate_example_ids": [],
            "missing_example_ids": [],
            "processed_success": [],
            "processed_failed": [],
            "skipped_already_done": [],
            "skipped_ineligible": list(skipped_rows),
        }
        input_registry_path = args.registry
    else:
        effective_where_validation_target = args.where_validation_target
        if effective_where_validation_target is None and not explicit_ids:
            effective_where_validation_target = "true"
        inputs, summary = collect_registry_inputs(
            registry_path=args.registry,
            runs_root=args.runs_root,
            example_ids=explicit_ids,
            where_final_status=args.where_final_status,
            where_validation_target=effective_where_validation_target,
            force=args.force,
            model_alias=config.primary_model,
            params_hash=params_hash,
        )
        input_registry_path = args.registry

    target_ids = summary["target_example_ids"]
    run_id, run_dir = create_run_directory(
        args.runs_root,
        STAGE_NAME,
        short_scope_from_ids(target_ids),
        dry_run=args.dry_run,
    )
    results_path = run_dir / "pair_validation_results.jsonl"
    artifact_paths = {"results_jsonl": str(results_path)}
    if args.output_jsonl:
        artifact_paths["legacy_output_jsonl"] = args.output_jsonl
    if args.output_doc:
        artifact_paths["legacy_output_doc"] = args.output_doc

    summary.update(
        {
            "run_id": run_id,
            "stage_name": STAGE_NAME,
            "parameters_hash": params_hash,
            "model_alias": config.primary_model,
            "artifact_paths": artifact_paths,
        }
    )

    if args.dry_run:
        for item in inputs:
            summary["processed_success"].append({"example_id": item.example_id, "dry_run": True})
        summary["status"] = summarize_run_status(
            summary["processed_success"],
            summary["processed_failed"],
            summary["skipped_already_done"],
            summary["skipped_ineligible"],
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    started_at = utc_timestamp()
    manifest = build_manifest(
        run_id=run_id,
        stage_name=STAGE_NAME,
        started_at=started_at,
        status="running",
        input_registry_path=input_registry_path,
        target_example_ids=target_ids,
        code_entrypoint="scripts/run_pair_validation.py",
        model_alias=config.primary_model,
        artifact_paths=artifact_paths,
        notes=["Run-folder mode is canonical. Legacy outputs are duplicate compatibility artifacts only."],
        backward_compatibility_mode=backward_compatibility_mode,
    )
    write_json(run_dir / "manifest.json", manifest)
    write_jsonl(results_path, [])

    validator = LlamaPairValidator(
        model_alias=config.primary_model,
        generation_settings=generation_settings,
    )
    model_load_error: Optional[str] = None
    if inputs:
        try:
            validator.load()
        except Exception as exc:
            model_load_error = str(exc)

    results_for_legacy: List[Dict[str, Any]] = []
    for item in inputs:
        if model_load_error:
            result: Dict[str, Any] = {
                "example_id": item.example_id,
                "model_alias": config.primary_model,
                "stage_name": STAGE_NAME,
                "parameters_hash": params_hash,
                "status": "failed",
                "notes": [model_load_error],
                "artifact_path": str(results_path),
            }
        else:
            try:
                result = validator.validate_pair(item)
                result["stage_name"] = STAGE_NAME
                result["parameters_hash"] = params_hash
                result["validation_gate_passed"] = validation_passed(result)
                result["status"] = "success" if result["validation_gate_passed"] else "failed"
                result["artifact_path"] = str(results_path)
            except Exception as exc:
                result = {
                    "example_id": item.example_id,
                    "model_alias": config.primary_model,
                    "stage_name": STAGE_NAME,
                    "parameters_hash": params_hash,
                    "status": "failed",
                    "notes": [str(exc)],
                    "artifact_path": str(results_path),
                }

        append_jsonl(results_path, result)
        results_for_legacy.append(result)

        if result.get("status") == "success":
            summary["processed_success"].append({"example_id": item.example_id, "artifact_path": str(results_path)})
        else:
            reason = compact_notes(result.get("notes", [])) if result.get("notes") else validation_notes(result, False)
            summary["processed_failed"].append({"example_id": item.example_id, "reason": reason, "artifact_path": str(results_path)})

        if not args.input_csv:
            try:
                if result.get("clean_reproduction_status") or result.get("corrupted_flip_status"):
                    updates = result_to_registry_updates(result, run_id, run_dir, results_path)
                else:
                    updates = failure_to_registry_updates(item.example_id, compact_notes(result.get("notes", [])), run_id, run_dir, results_path)
                update_registry_row(args.registry, item.example_id, updates, extra_fields=PAIR_REGISTRY_FIELDS)
            except KeyError:
                summary["skipped_ineligible"].append({"example_id": item.example_id, "reason": "result not written to registry because row is missing"})

    if args.output_jsonl:
        write_jsonl(args.output_jsonl, results_for_legacy)
    if args.output_doc:
        write_validation_markdown(
            results=results_for_legacy,
            skipped_rows=summary["skipped_ineligible"] + summary["skipped_already_done"],
            output_path=args.output_doc,
            input_csv_path=args.input_csv or args.registry,
            model_alias=config.primary_model,
            generation_settings=generation_settings,
            target_example_ids=target_ids,
        )

    summary["status"] = summarize_run_status(
        summary["processed_success"],
        summary["processed_failed"],
        summary["skipped_already_done"],
        summary["skipped_ineligible"],
    )
    summary["finished_at"] = utc_timestamp()
    write_json(run_dir / "summary.json", summary)
    manifest["finished_at"] = summary["finished_at"]
    manifest["status"] = summary["status"]
    write_json(run_dir / "manifest.json", manifest)

    print(f"Run ID: {run_id}")
    print(f"Run status: {summary['status']}")
    print(f"Run directory: {run_dir}")
    print(f"Success: {len(summary['processed_success'])} | Failed: {len(summary['processed_failed'])}")
    print(f"Skipped done: {len(summary['skipped_already_done'])} | Skipped ineligible: {len(summary['skipped_ineligible'])}")


if __name__ == "__main__":
    main()
