import argparse
import os
import sys
from typing import Any, Dict, List, Tuple


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tracing.head_ablation_pilot import (
    head_label,
    load_forward_pass_artifact,
    parse_head_label,
    run_head_ablation_pilot,
    load_top_heads_from_jsonl,
)
from src.workflow.run_artifacts import (
    build_manifest,
    create_run_directory,
    short_scope_from_ids,
    summarize_run_status,
    utc_timestamp,
    write_json,
)


STAGE_NAME = "head_ablation"
DEFAULT_RUNS_ROOT = "outputs/runs"
MODEL_ALIAS = "llama-2-7b-chat"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the single-example head ablation pilot.")
    parser.add_argument(
        "--input-pt",
        default="outputs/forward_pass_pilot.pt",
        help="Path to the forward-pass pilot .pt artifact.",
    )
    parser.add_argument(
        "--metadata",
        default="outputs/tracing_pilot_input.json",
        help="Path to the tracing metadata JSON file.",
    )
    parser.add_argument(
        "--head-patching-results",
        default="outputs/head_patching_results.jsonl",
        help="Path to the head patching JSONL output.",
    )
    parser.add_argument(
        "--heads",
        nargs="+",
        default=None,
        help="Optional head labels in priority order, e.g. --heads L29H5 L29H21 L31H4.",
    )
    parser.add_argument(
        "--runs-root",
        default=DEFAULT_RUNS_ROOT,
        help="Root directory for run-scoped artifacts.",
    )
    parser.add_argument(
        "--output-jsonl",
        default=None,
        help="Optional backward-compatible JSONL output path. Defaults to the run folder.",
    )
    parser.add_argument(
        "--output-doc",
        default=None,
        help="Optional backward-compatible Markdown output path. Defaults to the run folder.",
    )
    return parser.parse_args()


def parse_head_overrides(labels: List[str] | None) -> List[Tuple[int, int]] | None:
    if labels is None:
        return None
    return [parse_head_label(label) for label in labels]


def main() -> None:
    args = parse_args()
    artifact = load_forward_pass_artifact(args.input_pt)
    example_id = str(artifact.get("example_id", "")).strip()
    if not example_id:
        raise ValueError("Forward-pass artifact is missing example_id.")

    selected_heads = parse_head_overrides(args.heads)
    if selected_heads is None:
        selected_heads = load_top_heads_from_jsonl(
            args.head_patching_results,
            example_id=example_id,
            top_n=5,
        )

    run_id, run_dir = create_run_directory(
        args.runs_root,
        STAGE_NAME,
        short_scope_from_ids([example_id]),
    )
    output_jsonl_path = args.output_jsonl or str(run_dir / "head_ablation_results.jsonl")
    output_doc_path = args.output_doc or str(run_dir / "head_ablation_summary.md")
    artifact_paths = {
        "forward_pass_artifact": args.input_pt,
        "metadata": args.metadata,
        "head_patching_results": args.head_patching_results,
        "head_ablation_results": output_jsonl_path,
        "head_ablation_summary_md": output_doc_path,
    }

    started_at = utc_timestamp()
    manifest = build_manifest(
        run_id=run_id,
        stage_name=STAGE_NAME,
        started_at=started_at,
        status="running",
        input_registry_path="outputs/examples_registry.csv",
        target_example_ids=[example_id],
        code_entrypoint="scripts/run_head_ablation_pilot.py",
        model_alias=MODEL_ALIAS,
        artifact_paths=artifact_paths,
        notes=[
            "Head ablation only.",
            "Selected head slices are zeroed in the clean run at the clean causal prediction position.",
        ],
        backward_compatibility_mode=bool(args.output_jsonl or args.output_doc),
    )
    write_json(run_dir / "manifest.json", manifest)

    processed_success: list[Dict[str, Any]] = []
    processed_failed: list[Dict[str, Any]] = []
    try:
        result = run_head_ablation_pilot(
            input_pt_path=args.input_pt,
            metadata_path=args.metadata,
            head_patching_results_path=args.head_patching_results,
            output_jsonl_path=output_jsonl_path,
            output_doc_path=output_doc_path,
            model_alias=MODEL_ALIAS,
            selected_heads=selected_heads,
        )
        processed_success.append(
            {
                "example_id": result["summary"]["example_id"],
                "results_path": result["results_path"],
                "doc_path": result["doc_path"],
                "selected_heads": result["summary"]["selected_heads"],
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
        "selected_heads": [head_label(*head) for head in selected_heads],
        "processed_success": processed_success,
        "processed_failed": processed_failed,
        "skipped_already_done": [],
        "skipped_ineligible": [],
    }
    write_json(run_dir / "summary.json", summary)
    manifest["finished_at"] = finished_at
    manifest["status"] = status
    write_json(run_dir / "manifest.json", manifest)

    print(f"Run ID: {run_id}")
    print(f"Run status: {status}")
    print(f"Run directory: {run_dir}")
    print(f"Selected heads: {', '.join(summary['selected_heads'])}")
    print(f"Results JSONL: {output_jsonl_path}")
    print(f"Markdown summary: {output_doc_path}")
    print(f"Example retained: {example_id if processed_success else 'none'}")
    if processed_failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
