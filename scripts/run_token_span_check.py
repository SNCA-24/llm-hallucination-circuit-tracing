import argparse
import ast
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.workflow.run_artifacts import (
    append_jsonl,
    build_manifest,
    compact_notes,
    create_run_directory,
    find_successful_artifact,
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


STAGE_NAME = "token_span"
DEFAULT_REGISTRY = "outputs/examples_registry.csv"
DEFAULT_RUNS_ROOT = "outputs/runs"
DEFAULT_TOKENIZER = "NousResearch/Llama-2-7b-chat-hf"
TOKEN_REGISTRY_FIELDS = [
    "token_mapping_status",
    "token_mapping_known",
    "hallucinated_token_span",
    "first_hallucinated_token_index",
    "token_mapping_notes",
    "latest_run_id",
    "latest_artifact_root",
    "last_updated_stage",
    "latest_stage_status",
    "latest_stage_notes",
]
TERMINAL_TOKEN_STATUSES = {"clean", "ambiguous", "failed"}
PARKED_FINAL_STATUSES = {"parked", "processed_reject", "pilot_complete"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run token-span feasibility from the canonical registry.")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY, help="Canonical examples registry path.")
    parser.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT, help="Root directory for run-scoped artifacts.")
    parser.add_argument("--example-ids", nargs="+", default=None, help="Example IDs to process.")
    parser.add_argument("--where-final-status", default=None, help="Narrow selection to rows with this final_status.")
    parser.add_argument(
        "--where-validation-target",
        default=None,
        help="Narrow selection to validation_target_flag true/false.",
    )
    parser.add_argument("--force", action="store_true", help="Rerun terminal or previously completed examples.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run without writing artifacts or registry updates.")
    parser.add_argument("--tokenizer-name", default=DEFAULT_TOKENIZER, help="Fast tokenizer name or path.")
    parser.add_argument(
        "--output-jsonl",
        default=None,
        help="Backward-compatible duplicate JSONL output path. Run-folder output remains canonical.",
    )
    parser.add_argument(
        "--output-doc",
        default=None,
        help="Backward-compatible markdown summary output path. Only written when explicitly provided.",
    )
    return parser.parse_args()


def parse_char_span(raw_span: str) -> Tuple[int, int]:
    value = ast.literal_eval(str(raw_span).strip())
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"expected [start, end], got {raw_span!r}")
    start, end = int(value[0]), int(value[1])
    if start < 0 or end <= start:
        raise ValueError(f"invalid character span {raw_span!r}")
    return start, end


def row_is_terminal(row: Dict[str, str]) -> bool:
    return (
        str(row.get("token_mapping_status", "")).strip() in TERMINAL_TOKEN_STATUSES
        and str(row.get("token_mapping_known", "")).strip().casefold() == "yes"
    )


def missing_required_fields(row: Dict[str, str]) -> List[str]:
    missing = []
    if not str(row.get("original_response", "")).strip():
        missing.append("original_response")
    if not str(row.get("hallucinated_char_span", "")).strip():
        missing.append("hallucinated_char_span")
    return missing


def result_to_registry_updates(result: Dict[str, Any], run_id: str, run_dir: Path) -> Dict[str, Any]:
    if result.get("status") == "success":
        token_status = "clean" if result.get("clean") else "ambiguous"
        token_span = json.dumps(result.get("token_span") or [])
        first_token_index = result.get("first_token_index")
    else:
        token_status = "failed"
        token_span = ""
        first_token_index = ""

    notes = compact_notes(result.get("notes", []))
    return {
        "token_mapping_status": token_status,
        "token_mapping_known": "yes",
        "hallucinated_token_span": token_span,
        "first_hallucinated_token_index": first_token_index,
        "token_mapping_notes": notes,
        "latest_run_id": run_id,
        "latest_artifact_root": str(run_dir),
        "last_updated_stage": STAGE_NAME,
        "latest_stage_status": result.get("status", "failed"),
        "latest_stage_notes": notes,
    }


def write_legacy_markdown(
    output_path: str,
    *,
    tokenizer_name: str,
    results: Sequence[Dict[str, Any]],
    skipped: Sequence[Dict[str, Any]],
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    clean = sum(1 for item in results if item.get("status") == "success" and item.get("clean"))
    ambiguous = sum(1 for item in results if item.get("status") == "success" and not item.get("clean"))
    failed = sum(1 for item in results if item.get("status") != "success")
    with output.open("w", encoding="utf-8") as handle:
        handle.write("# Token Span Feasibility Check\n\n")
        handle.write(f"- Tokenizer: `{tokenizer_name}`\n")
        handle.write(f"- Results written for: {len(results)} examples\n")
        handle.write(f"- Clean mappings: {clean}\n")
        handle.write(f"- Ambiguous mappings: {ambiguous}\n")
        handle.write(f"- Failed mappings: {failed}\n")
        handle.write(f"- Skipped rows: {len(skipped)}\n\n")
        for result in results:
            handle.write(f"## Example {result.get('example_id')}\n")
            handle.write(f"- Status: `{result.get('status')}`\n")
            handle.write(f"- Notes: `{compact_notes(result.get('notes', []))}`\n\n")


def main() -> None:
    args = parse_args()
    rows, _fieldnames = read_registry(args.registry, extra_fields=TOKEN_REGISTRY_FIELDS)
    selection = select_registry_rows(
        rows,
        example_ids=args.example_ids,
        where_final_status=args.where_final_status,
        where_validation_target=args.where_validation_target,
    )
    target_ids = selection["target_example_ids"]
    short_scope = short_scope_from_ids(target_ids)
    parameters = {"tokenizer_name": args.tokenizer_name}
    params_hash = parameter_hash(parameters)
    run_id, run_dir = create_run_directory(args.runs_root, STAGE_NAME, short_scope, dry_run=args.dry_run)
    results_path = run_dir / "token_span_results.jsonl"
    artifact_paths = {"results_jsonl": str(results_path)}
    if args.output_jsonl:
        artifact_paths["legacy_output_jsonl"] = args.output_jsonl
    if args.output_doc:
        artifact_paths["legacy_output_doc"] = args.output_doc

    summary: Dict[str, Any] = {
        "run_id": run_id,
        "stage_name": STAGE_NAME,
        "parameters_hash": params_hash,
        "model_alias": None,
        "artifact_paths": artifact_paths,
        "target_example_ids": target_ids,
        "duplicate_example_ids": selection["duplicate_example_ids"],
        "missing_example_ids": selection["missing_example_ids"],
        "processed_success": [],
        "processed_failed": [],
        "skipped_already_done": [],
        "skipped_ineligible": [],
    }

    for example_id in selection["missing_example_ids"]:
        summary["skipped_ineligible"].append({"example_id": example_id, "reason": "example_id not present in registry"})
    for example_id in selection["filtered_out_example_ids"]:
        summary["skipped_ineligible"].append({"example_id": example_id, "reason": "filtered out by registry selection flags"})

    if args.dry_run:
        for row in selection["rows"]:
            example_id = str(row.get("example_id", "")).strip()
            if row_is_terminal(row) and not args.force:
                summary["skipped_already_done"].append({"example_id": example_id, "reason": "terminal token mapping status"})
                continue
            if str(row.get("final_status", "")).strip() in PARKED_FINAL_STATUSES and not args.force:
                summary["skipped_ineligible"].append({"example_id": example_id, "reason": "parked/rejected/final row requires --force"})
                continue
            missing = missing_required_fields(row)
            if missing:
                summary["skipped_ineligible"].append({"example_id": example_id, "reason": f"missing required field(s): {', '.join(missing)}"})
                continue
            prior_artifact = find_successful_artifact(
                args.runs_root,
                stage_name=STAGE_NAME,
                example_id=example_id,
                model_alias=None,
                parameters_hash=params_hash,
            )
            if prior_artifact and not args.force:
                summary["skipped_already_done"].append({"example_id": example_id, "reason": "matching prior successful artifact", "artifact_path": prior_artifact})
                continue
            summary["processed_success"].append({"example_id": example_id, "dry_run": True})
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
        input_registry_path=args.registry,
        target_example_ids=target_ids,
        code_entrypoint="scripts/run_token_span_check.py",
        artifact_paths=artifact_paths,
        notes=["Run-folder mode is canonical. Legacy outputs are duplicate compatibility artifacts only."],
        backward_compatibility_mode=bool(args.output_jsonl or args.output_doc),
    )
    write_json(run_dir / "manifest.json", manifest)
    write_jsonl(results_path, [])

    checker: Optional[Any] = None
    checker_cls: Optional[Any] = None
    results_for_legacy: List[Dict[str, Any]] = []

    for row in selection["rows"]:
        example_id = str(row.get("example_id", "")).strip()
        if row_is_terminal(row) and not args.force:
            summary["skipped_already_done"].append({"example_id": example_id, "reason": "terminal token mapping status"})
            continue
        if str(row.get("final_status", "")).strip() in PARKED_FINAL_STATUSES and not args.force:
            summary["skipped_ineligible"].append({"example_id": example_id, "reason": "parked/rejected/final row requires --force"})
            continue
        missing = missing_required_fields(row)
        if missing:
            summary["skipped_ineligible"].append({"example_id": example_id, "reason": f"missing required field(s): {', '.join(missing)}"})
            continue
        prior_artifact = find_successful_artifact(
            args.runs_root,
            stage_name=STAGE_NAME,
            example_id=example_id,
            model_alias=None,
            parameters_hash=params_hash,
        )
        if prior_artifact and not args.force:
            summary["skipped_already_done"].append({"example_id": example_id, "reason": "matching prior successful artifact", "artifact_path": prior_artifact})
            continue

        try:
            if checker is None:
                if checker_cls is None:
                    from src.replay.token_span_check import TokenSpanChecker

                    checker_cls = TokenSpanChecker
                checker = checker_cls(model_name=args.tokenizer_name)
            char_start, char_end = parse_char_span(row.get("hallucinated_char_span", ""))
            result = checker.check_span(row.get("original_response", ""), char_start, char_end)
            result["example_id"] = example_id
            result["stage_name"] = STAGE_NAME
            result["parameters_hash"] = params_hash
            result["artifact_path"] = str(results_path)
        except Exception as exc:
            result = {
                "example_id": example_id,
                "stage_name": STAGE_NAME,
                "parameters_hash": params_hash,
                "status": "failed",
                "notes": [str(exc)],
                "artifact_path": str(results_path),
            }

        append_jsonl(results_path, result)
        results_for_legacy.append(result)
        update_registry_row(
            args.registry,
            example_id,
            result_to_registry_updates(result, run_id, run_dir),
            extra_fields=TOKEN_REGISTRY_FIELDS,
        )

        if result.get("status") == "success":
            summary["processed_success"].append({"example_id": example_id, "artifact_path": str(results_path)})
        else:
            summary["processed_failed"].append({"example_id": example_id, "reason": compact_notes(result.get("notes", [])), "artifact_path": str(results_path)})

    if args.output_jsonl:
        write_jsonl(args.output_jsonl, results_for_legacy)
    if args.output_doc:
        write_legacy_markdown(
            args.output_doc,
            tokenizer_name=args.tokenizer_name,
            results=results_for_legacy,
            skipped=summary["skipped_already_done"] + summary["skipped_ineligible"],
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
