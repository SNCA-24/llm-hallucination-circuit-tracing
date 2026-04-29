import argparse
import csv
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


DEFAULT_INPUTS = [
    "outputs/pair_authoring_review_sheet.csv",
    "outputs/next_round_review_sheet_top3.csv",
]

REGISTRY_FIELDS = [
    # core identity
    "example_id",
    "source_id",
    "source_category",
    "task_type",
    "registry_source_files",
    # auxiliary lead provenance
    "candidate_source",
    "lead_match_status",
    "generation_metadata_source",
    "source_generation_temperature",
    "source_generation_notes",
    "ragtruth_response_id",
    "ragtruth_source_id",
    "ragtruth_model",
    "ragtruth_reproduction_verified",
    "ragtruth_new_behaviour_change",
    "lead_ingestion_notes",
    # static extracted fields
    "category",
    "why_shortlisted",
    "likely_divergence_type",
    "recommended_priority_rank",
    "minimal_edit_feasible",
    "raw_prompt_field",
    "raw_source_info_field",
    "clean_input_text_for_validation",
    "supporting_context_excerpt",
    "original_response",
    "raw_ground_truth_field",
    "hallucinated_substring",
    "hallucinated_char_span",
    "prompt_fallback_warning",
    # token mapping fields
    "token_mapping_status",
    "token_mapping_known",
    "hallucinated_token_span",
    "first_hallucinated_token_index",
    "token_mapping_notes",
    # human review fields
    "ground_truth_text_verified",
    "corrupted_prompt_candidate",
    "edit_class",
    "edit_delta_text",
    "why_minimal",
    "semantic_equivalence_check",
    "reviewer_notes",
    # validation fields
    "validation_target_flag",
    "clean_reproduction_status",
    "corrupted_flip_status",
    "validated_pair_flag",
    "validation_notes",
    "validation_results_path",
    # tracing fields
    "tracing_target_flag",
    "tracing_status",
    "built_clean_prompt",
    "built_corrupted_prompt",
    "tracing_notes",
    # workflow control fields
    "triage_status",
    "pair_authoring_status",
    "final_status",
    "keep_reason",
    "last_updated_stage",
    "latest_run_id",
    "latest_artifact_root",
    "latest_stage_status",
    "latest_stage_notes",
]


SOURCE_FIELD_MAP = {
    "example_id": "example_id",
    "source_id": "source_id",
    "source_category": "source_category",
    "task_type": "task_type",
    "candidate_source": "candidate_source",
    "lead_match_status": "lead_match_status",
    "generation_metadata_source": "generation_metadata_source",
    "source_generation_temperature": "source_generation_temperature",
    "ragtruth_temperature": "source_generation_temperature",
    "source_generation_notes": "source_generation_notes",
    "ragtruth_response_id": "ragtruth_response_id",
    "ragtruth_source_id": "ragtruth_source_id",
    "ragtruth_model": "ragtruth_model",
    "ragtruth_reproduction_verified": "ragtruth_reproduction_verified",
    "hallucination_reproduced_verified": "ragtruth_reproduction_verified",
    "ragtruth_new_behaviour_change": "ragtruth_new_behaviour_change",
    "category": "category",
    "predicted_category": "category",
    "why_shortlisted": "why_shortlisted",
    "short_reason_it_is_promising": "why_shortlisted",
    "likely_divergence_type": "likely_divergence_type",
    "recommended_priority_rank": "recommended_priority_rank",
    "minimal_edit_feasible": "minimal_edit_feasible",
    "raw_prompt_field": "raw_prompt_field",
    "raw_source_info_field": "raw_source_info_field",
    "clean_input_text_for_validation": "clean_input_text_for_validation",
    "supporting_context_excerpt": "supporting_context_excerpt",
    "original_response": "original_response",
    "raw_ground_truth_field": "raw_ground_truth_field",
    "hallucinated_substring": "hallucinated_substring",
    "hallucinated_char_span": "hallucinated_char_span",
    "prompt_fallback_warning": "prompt_fallback_warning",
    "token_mapping_status": "token_mapping_status",
    "token_mapping_known": "token_mapping_known",
    "hallucinated_token_span": "hallucinated_token_span",
    "first_hallucinated_token_index": "first_hallucinated_token_index",
    "ground_truth_text_verified": "ground_truth_text_verified",
    "corrupted_prompt_candidate": "corrupted_prompt_candidate",
    "edit_class": "edit_class",
    "edit_delta_text": "edit_delta_text",
    "why_minimal": "why_minimal",
    "semantic_equivalence_check": "semantic_equivalence_check",
    "clean_reproduction_status": "clean_reproduction_status",
    "corrupted_flip_status": "corrupted_flip_status",
    "reviewer_notes": "reviewer_notes",
    "latest_run_id": "latest_run_id",
    "latest_artifact_root": "latest_artifact_root",
    "latest_stage_status": "latest_stage_status",
    "latest_stage_notes": "latest_stage_notes",
}

LEAD_SHEET_KEYS = {
    "ragtruth_response_id",
    "ragtruth_source_id",
    "ragtruth_model",
    "ragtruth_temperature",
    "ragtruth_reproduction_verified",
    "hallucination_reproduced_verified",
    "ragtruth_new_behaviour_change",
    "match_confidence_notes",
    "candidate_source",
    "lead_match_status",
}

LIVE_PRESERVED_FIELDS = {
    "token_mapping_status",
    "token_mapping_known",
    "hallucinated_token_span",
    "first_hallucinated_token_index",
    "token_mapping_notes",
    "validation_target_flag",
    "clean_reproduction_status",
    "corrupted_flip_status",
    "validated_pair_flag",
    "validation_notes",
    "validation_results_path",
    "tracing_target_flag",
    "tracing_status",
    "built_clean_prompt",
    "built_corrupted_prompt",
    "tracing_notes",
    "final_status",
    "keep_reason",
    "last_updated_stage",
    "latest_run_id",
    "latest_artifact_root",
    "latest_stage_status",
    "latest_stage_notes",
}


KNOWN_OVERRIDES = {
    "369": {
        "token_mapping_status": "clean",
        "token_mapping_known": "yes",
        "validation_target_flag": "false",
        "clean_reproduction_status": "reproduced_hallucination",
        "corrupted_flip_status": "flipped_to_verified_truth",
        "validated_pair_flag": "true",
        "validation_notes": "Validated pilot pair from run 1.",
        "validation_results_path": "outputs/pair_validation_results_run1.jsonl",
        "tracing_target_flag": "true",
        "tracing_status": "pilot_complete",
        "tracing_notes": "Single-pair tracing pilot completed.",
        "triage_status": "processed_keep",
        "pair_authoring_status": "authored",
        "final_status": "pilot_complete",
        "keep_reason": "Validated pilot pair and completed tracing pilot.",
        "last_updated_stage": "tracing_pilot",
    },
    "51": {
        "token_mapping_status": "clean",
        "token_mapping_known": "yes",
        "validation_target_flag": "false",
        "clean_reproduction_status": "not_reproduced",
        "corrupted_flip_status": "truth_present_but_hallucination_still_present",
        "validated_pair_flag": "false",
        "validation_notes": "Failed validation in run 1.",
        "validation_results_path": "outputs/pair_validation_results_run1.jsonl",
        "tracing_target_flag": "false",
        "tracing_status": "not_started",
        "triage_status": "processed_reject",
        "pair_authoring_status": "authored",
        "final_status": "processed_reject",
        "keep_reason": "Validation failed: clean run did not reproduce and corrupted run retained the hallucinated substring.",
        "last_updated_stage": "pair_validation_run1",
    },
    "813": {
        "validation_target_flag": "true",
        "validated_pair_flag": "false",
        "tracing_target_flag": "false",
        "tracing_status": "not_started",
        "triage_status": "shortlisted",
        "pair_authoring_status": "authored",
        "final_status": "ready_for_validation",
        "keep_reason": "Clean token mapping and authored corrupted prompt for the next validation round.",
        "last_updated_stage": "pair_authoring",
    },
    "3573": {
        "validation_target_flag": "true",
        "validated_pair_flag": "false",
        "tracing_target_flag": "false",
        "tracing_status": "not_started",
        "triage_status": "shortlisted",
        "pair_authoring_status": "authored",
        "final_status": "ready_for_validation",
        "keep_reason": "Clean token mapping and authored corrupted prompt for the next validation round.",
        "last_updated_stage": "pair_authoring",
    },
    "2793": {
        "validation_target_flag": "false",
        "validated_pair_flag": "false",
        "tracing_target_flag": "false",
        "tracing_status": "not_started",
        "triage_status": "shortlisted",
        "pair_authoring_status": "authored",
        "final_status": "parked",
        "keep_reason": "Clean token mapping and authored prompt, but parked outside the current validation batch.",
        "last_updated_stage": "manual_review",
    },
    "2265": {
        "token_mapping_status": "ambiguous",
        "token_mapping_known": "yes",
        "validation_target_flag": "false",
        "validated_pair_flag": "false",
        "tracing_target_flag": "false",
        "tracing_status": "parked",
        "triage_status": "shortlisted",
        "pair_authoring_status": "not_started",
        "final_status": "parked",
        "keep_reason": "Token span mapping is ambiguous, so the example is parked.",
        "last_updated_stage": "token_span_check",
    },
    "2781": {
        "token_mapping_status": "ambiguous",
        "token_mapping_known": "yes",
        "validation_target_flag": "false",
        "validated_pair_flag": "false",
        "tracing_target_flag": "false",
        "tracing_status": "parked",
        "triage_status": "shortlisted",
        "pair_authoring_status": "not_started",
        "final_status": "parked",
        "keep_reason": "Token span mapping is ambiguous, so the example is parked.",
        "last_updated_stage": "token_span_check",
    },
}


def _is_non_empty(value: str) -> bool:
    return bool((value or "").strip())


def _blank_record() -> Dict[str, str]:
    return {field: "" for field in REGISTRY_FIELDS}


def _load_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_existing_registry(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    rows = _load_csv_rows(path)
    return {
        str(row.get("example_id", "")).strip(): row
        for row in rows
        if str(row.get("example_id", "")).strip()
    }


def _preserve_live_state(
    records: Sequence[Dict[str, str]],
    existing_registry: Dict[str, Dict[str, str]],
) -> int:
    preserved_rows = 0
    for record in records:
        example_id = str(record.get("example_id", "")).strip()
        existing = existing_registry.get(example_id)
        if not existing:
            continue
        preserved_any = False
        for field in LIVE_PRESERVED_FIELDS:
            if field in record and _is_non_empty(existing.get(field, "")):
                record[field] = existing[field]
                preserved_any = True
        if preserved_any:
            preserved_rows += 1
    return preserved_rows


def _append_note(record: Dict[str, str], field_name: str, value: str) -> None:
    value = (value or "").strip()
    if not value:
        return
    existing = (record.get(field_name) or "").strip()
    if not existing:
        record[field_name] = value
        return
    if value not in existing:
        record[field_name] = f"{existing} | {value}"


def _is_lead_row(row: Dict[str, str], source_name: str) -> bool:
    if "lead" in source_name.lower():
        return True
    return any(_is_non_empty(row.get(key, "")) for key in LEAD_SHEET_KEYS)


def _merge_source_row(
    record: Dict[str, str],
    row: Dict[str, str],
    source_name: str,
    *,
    is_lead_row: bool,
) -> None:
    source_files = set(filter(None, record["registry_source_files"].split(";")))
    source_files.add(source_name)
    record["registry_source_files"] = ";".join(sorted(source_files))

    for source_key, value in row.items():
        if is_lead_row and source_key in {"reviewer_notes", "match_confidence_notes"}:
            _append_note(record, "lead_ingestion_notes", value)
            continue
        if is_lead_row and source_key in {"original_response", "reproduced_response"}:
            continue
        target_key = SOURCE_FIELD_MAP.get(source_key)
        if target_key and _is_non_empty(value):
            record[target_key] = value.strip()

    if is_lead_row and not _is_non_empty(record.get("candidate_source", "")):
        record["candidate_source"] = "ragtruth_reproduced_lead"


def _infer_token_mapping_fields(record: Dict[str, str]) -> None:
    if not _is_non_empty(record["token_mapping_status"]):
        if _is_non_empty(record["hallucinated_token_span"]) and _is_non_empty(
            record["first_hallucinated_token_index"]
        ):
            record["token_mapping_status"] = "clean"
        else:
            record["token_mapping_status"] = "needs_checking"

    if not _is_non_empty(record["token_mapping_known"]):
        record["token_mapping_known"] = (
            "yes"
            if record["token_mapping_status"] in {"clean", "ambiguous", "failed"}
            else "no"
        )


def _apply_default_lead_fields(record: Dict[str, str]) -> None:
    if not _is_non_empty(record["candidate_source"]):
        record["candidate_source"] = "direct_xtended"

    if not _is_non_empty(record["lead_match_status"]):
        record["lead_match_status"] = (
            "not_applicable"
            if record["candidate_source"] == "direct_xtended"
            else "unmatched"
        )

    if not _is_non_empty(record["generation_metadata_source"]):
        if _is_non_empty(record["source_generation_temperature"]):
            record["generation_metadata_source"] = "ragtruth"
        elif record["candidate_source"] == "direct_xtended":
            record["generation_metadata_source"] = "xtended"
        else:
            record["generation_metadata_source"] = "unknown"


def _infer_pair_authoring_status(record: Dict[str, str]) -> str:
    required = (
        record["ground_truth_text_verified"],
        record["corrupted_prompt_candidate"],
        record["edit_class"],
    )
    if all(_is_non_empty(value) for value in required):
        return "authored"
    if any(_is_non_empty(value) for value in required):
        return "in_progress"
    return "not_started"


def _apply_default_workflow_status(record: Dict[str, str]) -> None:
    if not _is_non_empty(record["triage_status"]):
        record["triage_status"] = (
            "shortlisted"
            if _is_non_empty(record["why_shortlisted"]) or _is_non_empty(record["recommended_priority_rank"])
            else "unreviewed"
        )

    if not _is_non_empty(record["pair_authoring_status"]):
        record["pair_authoring_status"] = _infer_pair_authoring_status(record)

    if not _is_non_empty(record["validation_target_flag"]):
        record["validation_target_flag"] = "false"

    if not _is_non_empty(record["validated_pair_flag"]):
        record["validated_pair_flag"] = "false"

    if not _is_non_empty(record["tracing_target_flag"]):
        record["tracing_target_flag"] = "false"

    if not _is_non_empty(record["tracing_status"]):
        record["tracing_status"] = "not_started"

    if not _is_non_empty(record["final_status"]):
        if record["validated_pair_flag"] == "true":
            record["final_status"] = "validated"
        elif record["validation_target_flag"] == "true":
            record["final_status"] = "ready_for_validation"
        elif record["token_mapping_status"] == "ambiguous":
            record["final_status"] = "parked"
        elif record["pair_authoring_status"] == "authored":
            record["final_status"] = "authored_pending_validation"
        elif record["triage_status"] == "shortlisted":
            record["final_status"] = "shortlisted"
        else:
            record["final_status"] = "unreviewed"

    if not _is_non_empty(record["keep_reason"]):
        if record["final_status"] == "ready_for_validation":
            record["keep_reason"] = "Ready for the next pair-validation run."
        elif record["final_status"] == "parked":
            record["keep_reason"] = "Currently parked."
        elif record["final_status"] == "shortlisted":
            record["keep_reason"] = "Shortlisted for future review."

    if not _is_non_empty(record["last_updated_stage"]):
        if record["final_status"] == "ready_for_validation":
            record["last_updated_stage"] = "pair_authoring"
        elif record["token_mapping_status"] in {"clean", "ambiguous", "failed"}:
            record["last_updated_stage"] = "token_span_check"
        elif record["pair_authoring_status"] == "authored":
            record["last_updated_stage"] = "pair_authoring"
        else:
            record["last_updated_stage"] = "triage"


def _should_merge_lead_row(
    row: Dict[str, str],
    *,
    existing_registry: Dict[str, Dict[str, str]],
    allow_new_lead_rows: bool,
) -> bool:
    example_id = str(row.get("example_id", "")).strip()
    if not example_id:
        return False
    if example_id in existing_registry:
        return True
    return allow_new_lead_rows


def _build_registry(
    input_paths: Sequence[Path],
    *,
    allow_new_lead_rows: bool,
) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
    registry: Dict[str, Dict[str, str]] = {}
    stats = {
        "source_files_seen": 0,
        "lead_rows_seen": 0,
        "lead_rows_merged": 0,
        "lead_rows_skipped_pre_registry": 0,
    }

    for path in input_paths:
        if not path.exists():
            continue
        stats["source_files_seen"] += 1
        rows = _load_csv_rows(path)
        for row in rows:
            is_lead = _is_lead_row(row, path.name)
            if is_lead:
                stats["lead_rows_seen"] += 1
                if not _should_merge_lead_row(
                    row,
                    existing_registry=registry,
                    allow_new_lead_rows=allow_new_lead_rows,
                ):
                    stats["lead_rows_skipped_pre_registry"] += 1
                    continue
            example_id = str(row.get("example_id", "")).strip()
            if not example_id:
                continue
            record = registry.setdefault(example_id, _blank_record())
            record["example_id"] = example_id
            _merge_source_row(record, row, path.name, is_lead_row=is_lead)
            if is_lead:
                stats["lead_rows_merged"] += 1

    for example_id, record in registry.items():
        _apply_default_lead_fields(record)
        _infer_token_mapping_fields(record)
        _apply_default_workflow_status(record)
        for key, value in KNOWN_OVERRIDES.get(example_id, {}).items():
            record[key] = value

    records = sorted(
        registry.values(),
        key=lambda row: (int(row["example_id"]) if row["example_id"].isdigit() else row["example_id"]),
    )
    return records, stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the canonical examples registry.")
    parser.add_argument(
        "--input",
        action="append",
        dest="inputs",
        help="Additional CSV input to merge on top of the default active working sheets.",
    )
    parser.add_argument(
        "--allow-new-lead-rows",
        action="store_true",
        help=(
            "Allow a lead sheet to contribute brand-new registry rows when those rows already have an admitted "
            "example_id. By default, lead rows only augment existing admitted examples and otherwise stay pre-registry."
        ),
    )
    parser.add_argument(
        "--output",
        default="outputs/examples_registry.csv",
        help="Registry CSV output path.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Do a clean rebuild from source sheets and hardcoded defaults, discarding live state in the existing output registry.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    combined_inputs = list(DEFAULT_INPUTS)
    combined_inputs.extend(args.inputs or [])
    deduped_inputs = list(dict.fromkeys(combined_inputs))
    input_paths = [Path(path) for path in deduped_inputs]
    records, stats = _build_registry(
        input_paths,
        allow_new_lead_rows=args.allow_new_lead_rows,
    )

    output_path = Path(args.output)
    preserved_rows = 0
    if not args.reset:
        preserved_rows = _preserve_live_state(records, _load_existing_registry(output_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_FIELDS)
        writer.writeheader()
        writer.writerows(records)

    print(f"Rows written: {len(records)}")
    print(f"Registry output: {output_path}")
    print(f"Source files merged: {stats['source_files_seen']}")
    print(f"Lead rows seen: {stats['lead_rows_seen']}")
    print(f"Lead rows merged: {stats['lead_rows_merged']}")
    print(f"Lead rows skipped pre-registry: {stats['lead_rows_skipped_pre_registry']}")
    print(f"Existing live-state rows preserved: {preserved_rows}")
    if args.reset:
        print("Reset mode: existing live registry state was not preserved.")


if __name__ == "__main__":
    main()
