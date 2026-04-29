import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple


SUPPORTED_MODEL_ALIASES = {
    "llama-2-7b-chat": "NousResearch/Llama-2-7b-chat-hf",
}
DEFAULT_TOP_HEAD_COUNT = 5


def get_hf_token() -> str | None:
    for env_var in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HF_HUB_TOKEN"):
        value = os.environ.get(env_var)
        if value:
            return value

    try:
        from google.colab import userdata  # type: ignore

        value = userdata.get("HF_TOKEN")
        if value:
            return value
    except Exception:
        pass

    return None


def _lazy_import_torch():
    try:
        import torch
    except ImportError as exc:
        raise ImportError(
            "Head ablation pilot requires 'torch'. Install it in Colab before running this script."
        ) from exc
    return torch


def load_tracing_metadata(metadata_path: str) -> Dict[str, Any]:
    return json.loads(Path(metadata_path).read_text(encoding="utf-8"))


def load_forward_pass_artifact(input_path: str) -> Dict[str, Any]:
    torch = _lazy_import_torch()
    artifact = torch.load(input_path, map_location="cpu", weights_only=False)
    if artifact.get("model_alias") != "llama-2-7b-chat":
        raise ValueError("Head ablation pilot is locked to model_alias='llama-2-7b-chat'.")
    return artifact


def parse_head_label(head_label: str) -> Tuple[int, int]:
    if not head_label.startswith("L") or "H" not in head_label:
        raise ValueError(f"Invalid head label '{head_label}'. Expected form L<layer>H<head>.")
    layer_part, head_part = head_label[1:].split("H", 1)
    return int(layer_part), int(head_part)


def head_label(layer_index: int, head_index: int) -> str:
    return f"L{layer_index}H{head_index}"


def _require_matching_example_ids(artifact: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    artifact_example_id = str(artifact.get("example_id", "")).strip()
    metadata_example_id = str(metadata.get("example_id", "")).strip()
    if not artifact_example_id:
        raise ValueError("Forward-pass artifact is missing example_id.")
    if not metadata_example_id:
        raise ValueError("Tracing metadata is missing example_id.")
    if artifact_example_id != metadata_example_id:
        raise ValueError(
            "Forward-pass artifact and tracing metadata example IDs do not match: "
            f"{artifact_example_id!r} != {metadata_example_id!r}."
        )
    return artifact_example_id


def _require_clean_prediction_index(artifact: Dict[str, Any]) -> int:
    clean = artifact.get("clean", {})
    if clean.get("absolute_divergence_prediction_index") is None:
        raise ValueError("Forward-pass artifact is missing clean.absolute_divergence_prediction_index.")
    clean_prediction_index = int(clean["absolute_divergence_prediction_index"])
    if not clean.get("absolute_divergence_prediction_index_in_range"):
        raise ValueError("Clean absolute divergence prediction index is not marked in range.")
    seq_len = int(clean["input_token_ids"].shape[1])
    if not 0 <= clean_prediction_index < seq_len:
        raise ValueError(
            "Clean absolute divergence prediction index is outside the clean sequence: "
            f"{clean_prediction_index} not in [0, {seq_len})."
        )
    return clean_prediction_index


def _dedupe_heads(heads: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    seen = set()
    deduped = []
    for head in heads:
        if head in seen:
            continue
        seen.add(head)
        deduped.append(head)
    return deduped


def load_top_heads_from_jsonl(
    results_path: str,
    *,
    example_id: str,
    top_n: int | None = None,
) -> List[Tuple[int, int]]:
    rows: List[Dict[str, Any]] = []
    with open(results_path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if str(row.get("example_id", "")).strip() != str(example_id):
                continue
            rows.append(row)

    if not rows:
        raise ValueError(f"No head patching rows found for example {example_id}.")

    sorted_rows = sorted(rows, key=lambda row: row["restoration_score"], reverse=True)
    heads = [(int(row["layer_index"]), int(row["head_index"])) for row in sorted_rows]
    if top_n is not None:
        heads = heads[:top_n]
    return _dedupe_heads(heads)


def get_decoder_layers(model: Any) -> Any:
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        return model.model.layers
    if hasattr(model, "layers"):
        return model.layers
    raise AttributeError("Could not locate decoder layers on the loaded model.")


class HeadAblationPilotRunner:
    def __init__(self, model_alias: str = "llama-2-7b-chat"):
        if model_alias not in SUPPORTED_MODEL_ALIASES:
            raise ValueError(
                f"Unsupported model alias '{model_alias}'. "
                f"Supported aliases: {sorted(SUPPORTED_MODEL_ALIASES)}"
            )

        self.model_alias = model_alias
        self.model_name = SUPPORTED_MODEL_ALIASES[model_alias]
        self.torch = None
        self.tokenizer = None
        self.model = None
        self.device = None
        self.num_heads = None
        self.head_dim = None

    def load(self) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "Head ablation pilot requires 'torch' and 'transformers'. "
                "Install them in Colab before running this script."
            ) from exc

        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        hf_token = get_hf_token()
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            use_fast=True,
            token=hf_token,
        )
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        model_kwargs: Dict[str, Any] = {"low_cpu_mem_usage": True}
        if self.device == "cuda":
            model_kwargs["dtype"] = torch.float16
        if hf_token:
            model_kwargs["token"] = hf_token

        self.model = AutoModelForCausalLM.from_pretrained(self.model_name, **model_kwargs)
        self.model.to(self.device)
        self.model.eval()
        self.num_heads = int(self.model.config.num_attention_heads)
        self.head_dim = int(self.model.config.hidden_size // self.num_heads)

    def _ablate_heads(
        self,
        clean_input_ids: Any,
        clean_prediction_index: int,
        heads_to_ablate: List[Tuple[int, int]],
    ) -> Any:
        decoder_layers = get_decoder_layers(self.model)
        heads_by_layer: Dict[int, List[int]] = {}
        for layer_index, head_index in heads_to_ablate:
            heads_by_layer.setdefault(layer_index, []).append(head_index)

        hooks = []
        for layer_index, head_indices in heads_by_layer.items():
            head_slices = [
                (head_index * self.head_dim, (head_index + 1) * self.head_dim)
                for head_index in head_indices
            ]

            def make_hook(slices: List[Tuple[int, int]]):
                def hook(_module: Any, inputs: Any):
                    hidden = inputs[0].clone()
                    for start, end in slices:
                        hidden[:, clean_prediction_index, start:end] = 0.0
                    return (hidden,)

                return hook

            hooks.append(
                decoder_layers[layer_index].self_attn.o_proj.register_forward_pre_hook(
                    make_hook(head_slices)
                )
            )

        try:
            with self.torch.no_grad():
                outputs = self.model(
                    input_ids=clean_input_ids,
                    attention_mask=self.torch.ones_like(clean_input_ids, device=self.device),
                    return_dict=True,
                )
        finally:
            for hook in hooks:
                hook.remove()

        return outputs.logits.detach().cpu()


def build_ablation_record(
    example_id: str,
    setting_label: str,
    heads: List[Tuple[int, int]],
    baseline_hallucinated_token_logit: float,
    baseline_verified_truth_token_logit: float,
    ablated_hallucinated_token_logit: float,
    ablated_verified_truth_token_logit: float,
    ablation_score: float,
    hallucinated_token_id: int,
    verified_truth_token_id: int,
    hallucinated_token_text: str,
    verified_truth_token_text: str,
) -> Dict[str, Any]:
    return {
        "example_id": example_id,
        "setting_label": setting_label,
        "heads": [head_label(layer_index, head_index) for layer_index, head_index in heads],
        "num_heads": len(heads),
        "baseline_hallucinated_token_logit": baseline_hallucinated_token_logit,
        "baseline_verified_truth_token_logit": baseline_verified_truth_token_logit,
        "ablated_hallucinated_token_logit": ablated_hallucinated_token_logit,
        "ablated_verified_truth_token_logit": ablated_verified_truth_token_logit,
        "ablation_score": ablation_score,
        "hallucinated_token_id": hallucinated_token_id,
        "verified_truth_token_id": verified_truth_token_id,
        "hallucinated_token_text": hallucinated_token_text,
        "verified_truth_token_text": verified_truth_token_text,
    }


def write_results_jsonl(results: List[Dict[str, Any]], output_path: str) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result) + "\n")


def write_head_ablation_markdown(
    output_path: str,
    summary: Dict[str, Any],
    output_jsonl_path: str,
) -> None:
    doc_path = Path(output_path)
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    with doc_path.open("w", encoding="utf-8") as handle:
        handle.write("# Head Ablation Pilot\n\n")
        handle.write("## Scope\n")
        handle.write(f"- Retained example ID: `{summary['example_id']}`\n")
        handle.write(f"- Model scope: `{summary['model_alias']}` only\n")
        handle.write(
            "- Tested single heads: "
            + ", ".join(f"`{label}`" for label in summary["single_head_labels"])
            + "\n"
        )
        handle.write(
            "- Tested combinations: "
            + ", ".join(f"`{label}`" for label in summary["multi_head_setting_labels"])
            + "\n"
        )
        handle.write("- Phase boundary: destructive head ablation only; no multi-example or broad ablations yet\n\n")

        handle.write("## Best Single-Head Ablations\n")
        for record in summary["best_single_head_ablations"]:
            handle.write(
                f"- `{record['setting_label']}`: ablation score `{record['ablation_score']:.6f}`, "
                f"ablated truth logit `{record['ablated_verified_truth_token_logit']:.6f}`, "
                f"ablated hallucinated logit `{record['ablated_hallucinated_token_logit']:.6f}`\n"
            )
        handle.write("\n")

        handle.write("## Best Multi-Head Ablations\n")
        for record in summary["best_multi_head_ablations"]:
            handle.write(
                f"- `{record['setting_label']}`: ablation score `{record['ablation_score']:.6f}`, "
                f"heads `{record['heads']}`\n"
            )
        handle.write("\n")

        handle.write("## Hallucination Weakening Check\n")
        handle.write(
            f"- Any tested ablation increased truth-minus-hallucination margin: "
            f"`{summary['any_positive_ablation_score']}`\n"
        )
        handle.write(
            f"- Best observed ablation score: `{summary['best_observed_ablation_score']:.6f}`\n\n"
        )

        handle.write("## Output Artifact\n")
        handle.write(f"- Head ablation results JSONL: `{output_jsonl_path}`\n")


def build_ablation_settings(selected_heads: List[Tuple[int, int]]) -> List[Tuple[str, List[Tuple[int, int]]]]:
    selected_heads = _dedupe_heads(selected_heads)
    if not selected_heads:
        raise ValueError("No heads selected for ablation.")
    pair_heads = selected_heads[:2]
    top3 = selected_heads[:3]
    top5 = selected_heads[:5]
    settings: List[Tuple[str, List[Tuple[int, int]]]] = [
        (head_label(*head), [head]) for head in top5
    ]
    if len(pair_heads) >= 2:
        settings.append(
            (
                "pair_" + "_".join(head_label(*head) for head in pair_heads),
                pair_heads,
            )
        )
    if len(top3) >= 2:
        settings.append(("top3_heads", top3))
    if len(top5) >= 2:
        settings.append(("top5_heads", top5))
    return settings


def run_head_ablation_pilot(
    input_pt_path: str = "outputs/forward_pass_pilot.pt",
    metadata_path: str = "outputs/tracing_pilot_input.json",
    head_patching_results_path: str = "outputs/head_patching_results.jsonl",
    output_jsonl_path: str = "outputs/head_ablation_results.jsonl",
    output_doc_path: str = "docs/head_ablation_pilot.md",
    model_alias: str = "llama-2-7b-chat",
    selected_heads: List[Tuple[int, int]] | None = None,
) -> Dict[str, Any]:
    artifact = load_forward_pass_artifact(input_pt_path)
    metadata = load_tracing_metadata(metadata_path)
    example_id = _require_matching_example_ids(artifact, metadata)
    if artifact.get("model_alias") != model_alias:
        raise ValueError(f"Forward-pass artifact model_alias must be {model_alias!r}.")

    clean_prediction_index = _require_clean_prediction_index(artifact)

    required_artifact_fields = (
        "hallucinated_token_id_at_divergence",
        "verified_truth_token_id_at_divergence",
        "hallucinated_token_text_at_divergence",
        "verified_truth_token_text_at_divergence",
    )
    missing_fields = [field_name for field_name in required_artifact_fields if field_name not in artifact]
    if missing_fields:
        raise ValueError(
            "Forward-pass artifact is missing required divergence-token fields: "
            + ", ".join(missing_fields)
            + ". Rerun scripts/run_forward_pass_pilot.py before head ablation."
        )

    if selected_heads is None:
        selected_heads = load_top_heads_from_jsonl(
            head_patching_results_path,
            example_id=example_id,
            top_n=DEFAULT_TOP_HEAD_COUNT,
        )
    selected_heads = _dedupe_heads([(int(layer), int(head)) for layer, head in selected_heads])
    settings = build_ablation_settings(selected_heads)

    runner = HeadAblationPilotRunner(model_alias=model_alias)
    runner.load()

    token_info = {
        "hallucinated_token_id": int(artifact["hallucinated_token_id_at_divergence"]),
        "verified_truth_token_id": int(artifact["verified_truth_token_id_at_divergence"]),
        "hallucinated_token_text": artifact["hallucinated_token_text_at_divergence"],
        "verified_truth_token_text": artifact["verified_truth_token_text_at_divergence"],
    }

    clean_input_ids = artifact["clean"]["input_token_ids"].to(runner.device)
    clean_target_logits = artifact["clean"]["logits_at_absolute_divergence_prediction_position"]
    if clean_target_logits is None:
        raise ValueError("Forward-pass artifact is missing clean divergence-prediction logits.")
    clean_target_logits = clean_target_logits[0]

    baseline_hallucinated_token_logit = float(
        clean_target_logits[token_info["hallucinated_token_id"]].item()
    )
    baseline_verified_truth_token_logit = float(
        clean_target_logits[token_info["verified_truth_token_id"]].item()
    )
    baseline_margin = baseline_verified_truth_token_logit - baseline_hallucinated_token_logit

    results: List[Dict[str, Any]] = []
    for setting_label, heads in settings:
        ablated_logits = runner._ablate_heads(
            clean_input_ids=clean_input_ids,
            clean_prediction_index=clean_prediction_index,
            heads_to_ablate=heads,
        )
        ablated_target_logits = ablated_logits[:, clean_prediction_index, :][0]

        ablated_hallucinated_token_logit = float(
            ablated_target_logits[token_info["hallucinated_token_id"]].item()
        )
        ablated_verified_truth_token_logit = float(
            ablated_target_logits[token_info["verified_truth_token_id"]].item()
        )
        ablated_margin = ablated_verified_truth_token_logit - ablated_hallucinated_token_logit
        ablation_score = ablated_margin - baseline_margin

        results.append(
            build_ablation_record(
                example_id=example_id,
                setting_label=setting_label,
                heads=heads,
                baseline_hallucinated_token_logit=baseline_hallucinated_token_logit,
                baseline_verified_truth_token_logit=baseline_verified_truth_token_logit,
                ablated_hallucinated_token_logit=ablated_hallucinated_token_logit,
                ablated_verified_truth_token_logit=ablated_verified_truth_token_logit,
                ablation_score=ablation_score,
                hallucinated_token_id=token_info["hallucinated_token_id"],
                verified_truth_token_id=token_info["verified_truth_token_id"],
                hallucinated_token_text=token_info["hallucinated_token_text"],
                verified_truth_token_text=token_info["verified_truth_token_text"],
            )
        )

    write_results_jsonl(results, output_jsonl_path)

    single_head_results = [record for record in results if record["num_heads"] == 1]
    multi_head_results = [record for record in results if record["num_heads"] > 1]
    best_single = sorted(single_head_results, key=lambda record: record["ablation_score"], reverse=True)
    best_multi = sorted(multi_head_results, key=lambda record: record["ablation_score"], reverse=True)

    summary = {
        "example_id": example_id,
        "model_alias": model_alias,
        "selected_heads": [head_label(*head) for head in selected_heads],
        "single_head_labels": [label for label, heads in settings if len(heads) == 1],
        "multi_head_setting_labels": [label for label, heads in settings if len(heads) > 1],
        "clean_absolute_divergence_prediction_index": clean_prediction_index,
        "baseline_margin": baseline_margin,
        "best_single_head_ablations": best_single[:4],
        "best_multi_head_ablations": best_multi[:3],
        "any_positive_ablation_score": any(record["ablation_score"] > 0 for record in results),
        "best_observed_ablation_score": max(record["ablation_score"] for record in results),
    }
    write_head_ablation_markdown(
        output_path=output_doc_path,
        summary=summary,
        output_jsonl_path=output_jsonl_path,
    )

    return {
        "results_path": output_jsonl_path,
        "doc_path": output_doc_path,
        "summary": summary,
    }
