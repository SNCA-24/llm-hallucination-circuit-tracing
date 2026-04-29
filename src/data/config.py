from dataclasses import dataclass, field
from typing import Any, Dict, List

import yaml

@dataclass
class PilotConfig:
    project_root: str
    ragtruth_repo_path: str
    ragtruth_xtended_repo_path: str
    primary_model: str
    secondary_model: str
    hallucination_type: str
    primary_dataset: str
    supporting_dataset: str
    pilot_sample_size: int
    language_partition: str
    allowed_edit_classes: List[str]
    output_paths: Dict[str, str]
    generation_settings: Dict[str, Any] = field(default_factory=dict)
    pair_validation: Dict[str, Any] = field(default_factory=dict)

def load_config(config_path: str) -> PilotConfig:
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Config at {config_path} must deserialize to a mapping.")
    return PilotConfig(**data)
