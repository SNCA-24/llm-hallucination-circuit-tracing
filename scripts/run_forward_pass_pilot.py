import argparse
import os
import sys
from typing import Any, Dict


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tracing.forward_pass_pilot import load_tracing_pilot_input, run_forward_pass_pilot
from src.workflow.run_artifacts import (
    build_manifest,
    create_run_directory,
    short_scope_from_ids,
    summarize_run_status,
    utc_timestamp,
    write_json,
)


STAGE_NAME = "forward_pass"
DEFAULT_RUNS_ROOT = "outputs/runs"
MODEL_ALIAS = "llama-2-7b-chat"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the forward-pass tracing pilot.")
    parser.add_argument(
        "--input",
        default="outputs/tracing_pilot_input.json",
        help="Path to the tracing pilot JSON input.",
    )
    parser.add_argument(
        "--runs-root",
        default=DEFAULT_RUNS_ROOT,
        help="Root directory for run-scoped artifacts.",
    )
    parser.add_argument(
        "--output-pt",
        default=None,
        help="Optional backward-compatible .pt output path. Defaults to the run folder.",
    )
    parser.add_argument(
        "--output-doc",
        default=None,
        help="Optional backward-compatible Markdown output path. Defaults to the run folder.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = load_tracing_pilot_input(args.input)
    example_id = str(payload["example_id"])
    run_id, run_dir = create_run_directory(
        args.runs_root,
        STAGE_NAME,
        short_scope_from_ids([example_id]),
    )

    tensor_output_path = args.output_pt or str(run_dir / "forward_pass_pilot.pt")
    doc_output_path = args.output_doc or str(run_dir / "forward_pass_summary.md")
    updated_input_output_path = str(run_dir / "tracing_pilot_input_with_divergence.json")
    artifact_paths = {
        "input_tracing_pilot": args.input,
        "updated_tracing_pilot_input": updated_input_output_path,
        "forward_pass_tensor": tensor_output_path,
        "forward_pass_summary_md": doc_output_path,
    }
    if args.output_pt or args.output_doc:
        artifact_paths["backward_compatibility_note"] = "Explicit legacy output path supplied."

    started_at = utc_timestamp()
    manifest = build_manifest(
        run_id=run_id,
        stage_name=STAGE_NAME,
        started_at=started_at,
        status="running",
        input_registry_path="outputs/examples_registry.csv",
        target_example_ids=[example_id],
        code_entrypoint="scripts/run_forward_pass_pilot.py",
        model_alias=MODEL_ALIAS,
        artifact_paths=artifact_paths,
        notes=[
            "Forward pass only. Layer/head patching stages were not run.",
            "Model scope is llama-2-7b-chat only.",
        ],
        backward_compatibility_mode=bool(args.output_pt or args.output_doc),
    )
    write_json(run_dir / "manifest.json", manifest)

    processed_success: list[Dict[str, Any]] = []
    processed_failed: list[Dict[str, Any]] = []
    try:
        result = run_forward_pass_pilot(
            input_path=args.input,
            output_tensor_path=tensor_output_path,
            output_doc_path=doc_output_path,
            model_alias=MODEL_ALIAS,
            update_input_with_divergence=False,
            updated_input_output_path=updated_input_output_path,
        )
        processed_success.append(
            {
                "example_id": example_id,
                "tensor_output_path": result["tensor_output_path"],
                "doc_output_path": result["doc_output_path"],
            }
        )
    except Exception as exc:
        processed_failed.append({"example_id": example_id, "reason": str(exc)})

    status = summarize_run_status(processed_success, processed_failed)
    finished_at = utc_timestamp()
    summary = {
        "run_id": run_id,
        "stage_name": STAGE_NAME,
        "status": status,
        "finished_at": finished_at,
        "model_alias": MODEL_ALIAS,
        "artifact_paths": artifact_paths,
        "target_example_ids": [example_id],
        "retained_example_ids": [item["example_id"] for item in processed_success],
        "processed_success": processed_success,
        "processed_failed": processed_failed,
        "skipped_already_done": [],
        "skipped_ineligible": [],
        "layer_patching_run": False,
        "head_patching_run": False,
    }
    write_json(run_dir / "summary.json", summary)
    manifest["finished_at"] = finished_at
    manifest["status"] = status
    write_json(run_dir / "manifest.json", manifest)

    print(f"Run ID: {run_id}")
    print(f"Run status: {status}")
    print(f"Run directory: {run_dir}")
    print(f"Tensor output: {tensor_output_path}")
    print(f"Markdown summary: {doc_output_path}")
    print(f"Example retained: {example_id if processed_success else 'none'}")
    if processed_failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
