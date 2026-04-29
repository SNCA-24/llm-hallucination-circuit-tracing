import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from scripts.build_examples_registry import _preserve_live_state


class BuildExamplesRegistryTests(unittest.TestCase):
    def test_preserve_live_state_keeps_stage_written_fields(self) -> None:
        records = [
            {
                "example_id": "813",
                "validation_target_flag": "true",
                "validated_pair_flag": "false",
                "final_status": "ready_for_validation",
                "latest_run_id": "",
                "keep_reason": "source default",
            }
        ]
        existing = {
            "813": {
                "example_id": "813",
                "validation_target_flag": "false",
                "validated_pair_flag": "true",
                "final_status": "validated",
                "latest_run_id": "20260425_223900_pair_validation_813_3573",
                "keep_reason": "Validated clean/corrupted pair.",
            }
        }

        preserved = _preserve_live_state(records, existing)

        self.assertEqual(preserved, 1)
        self.assertEqual(records[0]["validation_target_flag"], "false")
        self.assertEqual(records[0]["validated_pair_flag"], "true")
        self.assertEqual(records[0]["final_status"], "validated")
        self.assertEqual(records[0]["latest_run_id"], "20260425_223900_pair_validation_813_3573")
        self.assertEqual(records[0]["keep_reason"], "Validated clean/corrupted pair.")


if __name__ == "__main__":
    unittest.main()
