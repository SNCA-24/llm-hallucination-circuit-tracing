import csv
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback.
    fcntl = None


RUN_TRACKING_FIELDS = [
    "latest_run_id",
    "latest_artifact_root",
    "latest_stage_status",
    "latest_stage_notes",
]

TERMINAL_RUN_STATUSES = {"success", "partial", "failed", "skipped", "no_op"}


def utc_timestamp() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", str(value or "").strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "run"


def short_scope_from_ids(example_ids: Sequence[str], fallback: str = "registry") -> str:
    ids = [str(example_id).strip() for example_id in example_ids if str(example_id).strip()]
    if not ids:
        return fallback
    if len(ids) == 1:
        return ids[0]
    return f"{ids[0]}_{ids[-1]}"


def build_run_id(stage_name: str, short_scope: str, now: Optional[datetime] = None) -> str:
    timestamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{_slug(stage_name)}_{_slug(short_scope)}"


def unique_run_id(base_run_id: str, runs_root: Path) -> str:
    candidate = base_run_id
    suffix = 2
    while (runs_root / candidate).exists():
        candidate = f"{base_run_id}_{suffix}"
        suffix += 1
    return candidate


def create_run_directory(
    runs_root: str | Path,
    stage_name: str,
    short_scope: str,
    *,
    dry_run: bool = False,
    now: Optional[datetime] = None,
) -> Tuple[str, Path]:
    root = Path(runs_root)
    base_run_id = build_run_id(stage_name, short_scope, now=now)
    run_id = unique_run_id(base_run_id, root)
    run_dir = root / run_id
    if not dry_run:
        run_dir.mkdir(parents=True, exist_ok=False)
    return run_id, run_dir


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def append_jsonl(path: str | Path, payload: Dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def write_jsonl(path: str | Path, rows: Sequence[Dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def parameter_hash(parameters: Dict[str, Any]) -> str:
    canonical = json.dumps(parameters, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def dedupe_preserve_order(values: Optional[Sequence[Any]]) -> Tuple[List[str], List[str]]:
    if not values:
        return [], []
    seen = set()
    deduped: List[str] = []
    duplicates: List[str] = []
    for value in values:
        item = str(value).strip()
        if not item:
            continue
        if item in seen:
            duplicates.append(item)
            continue
        seen.add(item)
        deduped.append(item)
    return deduped, duplicates


def normalize_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    text = str(value).strip().casefold()
    if text == "":
        return False
    if text in {"true", "t", "yes", "y", "1"}:
        return True
    if text in {"false", "f", "no", "n", "0"}:
        return False
    raise ValueError(f"Expected a boolean-like value, got: {value!r}")


def bool_to_registry(value: bool) -> str:
    return "true" if value else "false"


def is_non_empty(value: Any) -> bool:
    return bool(str(value or "").strip())


def _read_registry_unlocked(path: str | Path, extra_fields: Optional[Sequence[str]] = None) -> Tuple[List[Dict[str, str]], List[str]]:
    registry_path = Path(path)
    with registry_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]

    for field in list(extra_fields or []) + RUN_TRACKING_FIELDS:
        if field not in fieldnames:
            fieldnames.append(field)

    for row in rows:
        for field in fieldnames:
            row.setdefault(field, "")
    return rows, fieldnames


def read_registry(path: str | Path, extra_fields: Optional[Sequence[str]] = None) -> Tuple[List[Dict[str, str]], List[str]]:
    return _read_registry_unlocked(path, extra_fields=extra_fields)


@contextmanager
def _registry_lock(path: Path):
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock_handle:
        if fcntl is not None:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _write_registry_unlocked(path: str | Path, rows: Sequence[Dict[str, str]], fieldnames: Sequence[str]) -> None:
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        dir=str(registry_path.parent),
        delete=False,
    ) as tmp_handle:
        writer = csv.DictWriter(tmp_handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
        tmp_path = tmp_handle.name
    os.replace(tmp_path, registry_path)


def write_registry(path: str | Path, rows: Sequence[Dict[str, str]], fieldnames: Sequence[str]) -> None:
    registry_path = Path(path)
    with _registry_lock(registry_path):
        _write_registry_unlocked(registry_path, rows, fieldnames)


def update_registry_row(
    registry_path: str | Path,
    example_id: str,
    updates: Dict[str, Any],
    *,
    extra_fields: Optional[Sequence[str]] = None,
) -> None:
    path = Path(registry_path)
    with _registry_lock(path):
        rows, fieldnames = _read_registry_unlocked(path, extra_fields=extra_fields)
        target = str(example_id)
        found = False
        for row in rows:
            if str(row.get("example_id", "")).strip() == target:
                for key, value in updates.items():
                    if key not in fieldnames:
                        fieldnames.append(key)
                        for existing in rows:
                            existing.setdefault(key, "")
                    row[key] = "" if value is None else str(value)
                found = True
                break
        if not found:
            raise KeyError(f"example_id {example_id!r} not found in registry")
        _write_registry_unlocked(path, rows, fieldnames)


def select_registry_rows(
    rows: Sequence[Dict[str, str]],
    *,
    example_ids: Optional[Sequence[str]] = None,
    where_final_status: Optional[str] = None,
    where_validation_target: Optional[Any] = None,
) -> Dict[str, Any]:
    deduped_ids, duplicate_ids = dedupe_preserve_order(example_ids)
    all_by_id = {str(row.get("example_id", "")).strip(): row for row in rows}

    validation_target_bool = normalize_bool(where_validation_target)

    def matches(row: Dict[str, str]) -> bool:
        if where_final_status is not None and str(row.get("final_status", "")).strip() != where_final_status:
            return False
        if validation_target_bool is not None:
            row_value = normalize_bool(row.get("validation_target_flag", "false"))
            if row_value != validation_target_bool:
                return False
        return True

    filtered_rows = [row for row in rows if matches(row)]
    filtered_by_id = {str(row.get("example_id", "")).strip(): row for row in filtered_rows}

    if deduped_ids:
        selected = [filtered_by_id[example_id] for example_id in deduped_ids if example_id in filtered_by_id]
        missing_ids = [example_id for example_id in deduped_ids if example_id not in all_by_id]
        filtered_out_ids = [
            example_id
            for example_id in deduped_ids
            if example_id in all_by_id and example_id not in filtered_by_id
        ]
        target_ids = deduped_ids
    else:
        selected = filtered_rows
        missing_ids = []
        filtered_out_ids = []
        target_ids = [str(row.get("example_id", "")).strip() for row in selected]

    return {
        "rows": selected,
        "target_example_ids": target_ids,
        "duplicate_example_ids": duplicate_ids,
        "missing_example_ids": missing_ids,
        "filtered_out_example_ids": filtered_out_ids,
    }


def summarize_run_status(
    processed_success: Sequence[Any],
    processed_failed: Sequence[Any],
    skipped_already_done: Optional[Sequence[Any]] = None,
    skipped_ineligible: Optional[Sequence[Any]] = None,
) -> str:
    if processed_success and processed_failed:
        return "partial"
    if processed_success and not processed_failed:
        return "success"
    if processed_failed:
        return "failed"
    if skipped_already_done or skipped_ineligible:
        return "skipped"
    return "failed"


def build_manifest(
    *,
    run_id: str,
    stage_name: str,
    started_at: str,
    input_registry_path: str,
    target_example_ids: Sequence[str],
    code_entrypoint: str,
    model_alias: Optional[str] = None,
    artifact_paths: Optional[Dict[str, str]] = None,
    notes: Optional[Sequence[str]] = None,
    backward_compatibility_mode: bool = False,
    status: str = "running",
    finished_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "stage_name": stage_name,
        "started_at": started_at,
        "finished_at": finished_at,
        "status": status,
        "input_registry_path": input_registry_path,
        "target_example_ids": list(target_example_ids),
        "model_alias": model_alias,
        "code_entrypoint": code_entrypoint,
        "artifact_paths": artifact_paths or {},
        "notes": list(notes or []),
        "backward_compatibility_mode": bool(backward_compatibility_mode),
    }


def read_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_failed_ids_from_run(run_dir: str | Path) -> List[str]:
    summary_path = Path(run_dir) / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"No summary.json found under {run_dir}")
    with summary_path.open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    ids: List[str] = []
    for item in summary.get("processed_failed", []):
        if isinstance(item, dict):
            example_id = item.get("example_id")
        else:
            example_id = item
        if example_id is not None:
            ids.append(str(example_id))
    return ids


def find_successful_artifact(
    runs_root: str | Path,
    *,
    stage_name: str,
    example_id: str,
    model_alias: Optional[str],
    parameters_hash: str,
) -> Optional[str]:
    root = Path(runs_root)
    if not root.exists():
        return None

    for summary_path in sorted(root.glob("*/summary.json"), reverse=True):
        try:
            with summary_path.open("r", encoding="utf-8") as handle:
                summary = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        if summary.get("stage_name") != stage_name:
            continue
        if summary.get("parameters_hash") != parameters_hash:
            continue
        if model_alias is not None and summary.get("model_alias") != model_alias:
            continue
        for item in summary.get("processed_success", []):
            if isinstance(item, dict) and str(item.get("example_id")) == str(example_id):
                path = item.get("artifact_path") or summary.get("artifact_paths", {}).get("results_jsonl")
                if path and Path(path).exists():
                    return str(path)
    return None


def compact_notes(notes: Iterable[Any], limit: int = 240) -> str:
    text = " | ".join(str(note).strip() for note in notes if str(note or "").strip())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
