import csv
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.workflow.run_artifacts import (
    RUN_TRACKING_FIELDS,
    build_run_id,
    create_run_directory,
    normalize_bool,
    read_registry,
    select_registry_rows,
    summarize_run_status,
    unique_run_id,
    update_registry_row,
)


class RunArtifactsTests(unittest.TestCase):
    def test_run_id_collision_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            runs_root = Path(tmp_dir)
            base = build_run_id(
                "pair_validation",
                "813_3573",
                now=datetime(2026, 4, 25, 22, 39, 0),
            )
            (runs_root / base).mkdir()
            self.assertEqual(base, "20260425_223900_pair_validation_813_3573")
            self.assertEqual(unique_run_id(base, runs_root), f"{base}_2")

    def test_create_run_directory_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_id, run_dir = create_run_directory(
                tmp_dir,
                "token_span",
                "813_3573",
                dry_run=True,
                now=datetime(2026, 4, 25, 22, 15, 30),
            )
            self.assertEqual(run_id, "20260425_221530_token_span_813_3573")
            self.assertFalse(run_dir.exists())

    def test_registry_normalization_and_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            registry_path = Path(tmp_dir) / "registry.csv"
            with registry_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["example_id", "final_status"])
                writer.writeheader()
                writer.writerow({"example_id": "813", "final_status": "ready_for_validation"})

            rows, fieldnames = read_registry(registry_path)
            for field in RUN_TRACKING_FIELDS:
                self.assertIn(field, fieldnames)
                self.assertEqual(rows[0][field], "")

            update_registry_row(registry_path, "813", {"latest_run_id": "run_1"})
            rows, _fieldnames = read_registry(registry_path)
            self.assertEqual(rows[0]["latest_run_id"], "run_1")

    def test_selection_filters_and_duplicate_ids(self) -> None:
        rows = [
            {"example_id": "813", "final_status": "ready_for_validation", "validation_target_flag": "true"},
            {"example_id": "3573", "final_status": "ready_for_validation", "validation_target_flag": "false"},
            {"example_id": "369", "final_status": "pilot_complete", "validation_target_flag": "false"},
        ]
        selection = select_registry_rows(
            rows,
            example_ids=["813", "813", "3573", "999"],
            where_final_status="ready_for_validation",
            where_validation_target="true",
        )
        self.assertEqual([row["example_id"] for row in selection["rows"]], ["813"])
        self.assertEqual(selection["duplicate_example_ids"], ["813"])
        self.assertEqual(selection["missing_example_ids"], ["999"])
        self.assertEqual(selection["filtered_out_example_ids"], ["3573"])

    def test_summary_status(self) -> None:
        self.assertEqual(summarize_run_status([{"example_id": "813"}], []), "success")
        self.assertEqual(summarize_run_status([{"example_id": "813"}], [{"example_id": "3573"}]), "partial")
        self.assertEqual(summarize_run_status([], [{"example_id": "3573"}]), "failed")
        self.assertEqual(summarize_run_status([], [], [{"example_id": "813"}], []), "skipped")
        self.assertEqual(summarize_run_status([], []), "failed")

    def test_blank_bool_fields_are_false_for_filtering(self) -> None:
        self.assertFalse(normalize_bool(""))
        rows = [
            {"example_id": "813", "final_status": "ready_for_validation", "validation_target_flag": ""},
            {"example_id": "3573", "final_status": "ready_for_validation", "validation_target_flag": "true"},
        ]
        selection = select_registry_rows(rows, where_validation_target="false")
        self.assertEqual([row["example_id"] for row in selection["rows"]], ["813"])


if __name__ == "__main__":
    unittest.main()
