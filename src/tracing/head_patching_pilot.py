import json
import os
from pathlib import Path
from typing import Any, Dict, List


SUPPORTED_MODEL_ALIASES = {
    "llama-2-7b-chat": "NousResearch/Llama-2-7b-chat-hf",
}

DEFAULT_TOP_LAYER_COUNT = 3


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
            "Head patching pilot requires 'torch'. Install it in Colab before running this script."
        ) from exc
    return torch


def load_tracing_metadata(metadata_path: str) -> Dict[str, Any]:
    return json.loads(Path(metadata_path).read_text(encoding="utf-8"))


def load_forward_pass_artifact(input_path: str) -> Dict[str, Any]:
    torch = _lazy_import_torch()
    artifact = torch.load(input_path, map_location="cpu", weights_only=False)
    if artifact.get("model_alias") != "llama-2-7b-chat":
        raise ValueError("Head patching pilot is locked to model_alias='llama-2-7b-chat'.")
    return artifact


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def select_top_layers_from_results(
    layer_results_path: str,
    *,
    example_id: str,
    top_n: int = DEFAULT_TOP_LAYER_COUNT,
) -> List[int]:
    records = [
        record
        for record in load_jsonl(layer_results_path)
        if str(record.get("example_id", "")).strip() == str(example_id)
    ]
    if not records:
        raise ValueError(f"No layer patching rows found for example {example_id}.")
    top_records = sorted(records, key=lambda record: float(record["restoration_score"]), reverse=True)[:top_n]
    return [int(record["layer_index"]) for record in top_records]


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


def _require_int(value: Any, field_name: str) -> int:
    if value is None:
        raise ValueError(f"Forward-pass artifact is missing {field_name}.")
    return int(value)


def _require_prediction_indices(artifact: Dict[str, Any]) -> Dict[str, int]:
    clean = artifact.get("clean", {})
    corrupted = artifact.get("corrupted", {})
    clean_prediction_index = _require_int(
        clean.get("absolute_divergence_prediction_index"),
        "clean.absolute_divergence_prediction_index",
    )
    corrupted_prediction_index = _require_int(
        corrupted.get("absolute_divergence_prediction_index"),
        "corrupted.absolute_divergence_prediction_index",
    )
    if not clean.get("absolute_divergence_prediction_index_in_range"):
        raise ValueError("Clean absolute divergence prediction index is not marked in range.")
    if not corrupted.get("absolute_divergence_prediction_index_in_range"):
        raise ValueError("Corrupted absolute divergence prediction index is not marked in range.")

    clean_seq_len = int(clean["input_token_ids"].shape[1])
    corrupted_seq_len = int(corrupted["input_token_ids"].shape[1])
    if not 0 <= clean_prediction_index < clean_seq_len:
        raise ValueError(
            "Clean absolute divergence prediction index is outside the clean sequence: "
            f"{clean_prediction_index} not in [0, {clean_seq_len})."
        )
    if not 0 <= corrupted_prediction_index < corrupted_seq_len:
        raise ValueError(
            "Corrupted absolute divergence prediction index is outside the corrupted sequence: "
            f"{corrupted_prediction_index} not in [0, {corrupted_seq_len})."
        )
    return {
        "clean_prediction_index": clean_prediction_index,
        "corrupted_prediction_index": corrupted_prediction_index,
    }


def get_decoder_layers(model: Any) -> Any:
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        return model.model.layers
    if hasattr(model, "layers"):
        return model.layers
    raise AttributeError("Could not locate decoder layers on the loaded model.")


class HeadPatchingPilotRunner:
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
                "Head patching pilot requires 'torch' and 'transformers'. "
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

    def _capture_corrupted_head_inputs(
        self,
        corrupted_input_ids: Any,
        target_layers: List[int],
        corrupted_absolute_prediction_index: int,
    ) -> Dict[int, Any]:
        decoder_layers = get_decoder_layers(self.model)
        captured: Dict[int, Any] = {}

        def make_hook(layer_index: int):
            def hook(_module: Any, inputs: Any) -> None:
                hidden = inputs[0].detach().cpu()
                captured[layer_index] = hidden[:, corrupted_absolute_prediction_index, :].clone()

            return hook

        hooks = [
            decoder_layers[layer_index].self_attn.o_proj.register_forward_pre_hook(make_hook(layer_index))
            for layer_index in target_layers
        ]
        try:
            with self.torch.no_grad():
                self.model(
                    input_ids=corrupted_input_ids,
                    attention_mask=self.torch.ones_like(corrupted_input_ids, device=self.device),
                    return_dict=True,
                )
        finally:
            for hook in hooks:
                hook.remove()

        return captured

    def _patch_single_head(
        self,
        layer_index: int,
        head_index: int,
        clean_input_ids: Any,
        clean_absolute_prediction_index: int,
        donor_hidden: Any,
    ) -> Any:
        decoder_layers = get_decoder_layers(self.model)
        head_start = head_index * self.head_dim
        head_end = head_start + self.head_dim
        donor_hidden = donor_hidden.to(device=self.device, dtype=self.model.dtype)

        def patch_hook(_module: Any, inputs: Any):
            hidden = inputs[0].clone()
            hidden[:, clean_absolute_prediction_index, head_start:head_end] = donor_hidden[
                :, head_start:head_end
            ]
            return (hidden,)

        hook = decoder_layers[layer_index].self_attn.o_proj.register_forward_pre_hook(patch_hook)
        try:
            with self.torch.no_grad():
                outputs = self.model(
                    input_ids=clean_input_ids,
                    attention_mask=self.torch.ones_like(clean_input_ids, device=self.device),
                    return_dict=True,
                )
        finally:
            hook.remove()

        return outputs.logits.detach().cpu()


def build_head_result_record(
    example_id: str,
    layer_index: int,
    head_index: int,
    baseline_hallucinated_token_logit: float,
    baseline_verified_truth_token_logit: float,
    patched_hallucinated_token_logit: float,
    patched_verified_truth_token_logit: float,
    restoration_score: float,
    hallucinated_token_id: int,
    verified_truth_token_id: int,
    hallucinated_token_text: str,
    verified_truth_token_text: str,
) -> Dict[str, Any]:
    return {
        "example_id": example_id,
        "layer_index": layer_index,
        "head_index": head_index,
        "baseline_hallucinated_token_logit": baseline_hallucinated_token_logit,
        "baseline_verified_truth_token_logit": baseline_verified_truth_token_logit,
        "patched_hallucinated_token_logit": patched_hallucinated_token_logit,
        "patched_verified_truth_token_logit": patched_verified_truth_token_logit,
        "restoration_score": restoration_score,
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


def write_head_patching_markdown(
    output_path: str,
    summary: Dict[str, Any],
    input_pt_path: str,
    output_jsonl_path: str,
) -> None:
    doc_path = Path(output_path)
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    with doc_path.open("w", encoding="utf-8") as handle:
        handle.write("# Head Patching Pilot\n\n")
        handle.write("## Scope\n")
        handle.write(f"- Input artifact: `{input_pt_path}`\n")
        handle.write(f"- Retained example ID: `{summary['example_id']}`\n")
        handle.write(f"- Model scope: `{summary['model_alias']}` only\n")
        handle.write(
            "- Restricted layers: "
            + ", ".join(f"`{layer_index}`" for layer_index in summary["target_layers"])
            + "\n"
        )
        handle.write("- Phase boundary: head-wise patching only; no ablations yet\n\n")

        handle.write("## Top Restoring Heads Overall\n")
        for record in summary["top_heads_overall"]:
            handle.write(
                f"- Layer `{record['layer_index']}`, head `{record['head_index']}`: "
                f"restoration score `{record['restoration_score']:.6f}`, "
                f"patched truth logit `{record['patched_verified_truth_token_logit']:.6f}`, "
                f"patched hallucinated logit `{record['patched_hallucinated_token_logit']:.6f}`\n"
            )
        handle.write("\n")

        handle.write("## Top Restoring Heads Per Layer\n")
        for layer_index, records in summary["top_heads_per_layer"].items():
            if not records:
                handle.write(f"- Layer `{layer_index}`: no results\n")
                continue
            best = records[0]
            handle.write(
                f"- Layer `{layer_index}` best head `{best['head_index']}` "
                f"with restoration score `{best['restoration_score']:.6f}`\n"
            )
        handle.write("\n")

        strongest = ", ".join(
            f"L{record['layer_index']}H{record['head_index']}"
            for record in summary["top_heads_overall"][:5]
        )
        handle.write("## Candidate Heads\n")
        handle.write(
            f"- Strongest candidate heads from this single-pair pilot: `{strongest}`\n\n"
        )

        handle.write("## Output Artifact\n")
        handle.write(f"- Head results JSONL: `{output_jsonl_path}`\n")


def run_head_patching_pilot(
    input_pt_path: str = "outputs/forward_pass_pilot.pt",
    metadata_path: str = "outputs/tracing_pilot_input.json",
    layer_results_path: str = "outputs/layer_patching_results.jsonl",
    output_jsonl_path: str = "outputs/head_patching_results.jsonl",
    output_doc_path: str = "docs/head_patching_pilot.md",
    model_alias: str = "llama-2-7b-chat",
    target_layers: List[int] | None = None,
) -> Dict[str, Any]:
    artifact = load_forward_pass_artifact(input_pt_path)
    metadata = load_tracing_metadata(metadata_path)

    example_id = _require_matching_example_ids(artifact, metadata)
    if artifact.get("model_alias") != model_alias:
        raise ValueError(f"Forward-pass artifact model_alias must be {model_alias!r}.")

    prediction_indices = _require_prediction_indices(artifact)
    clean_prediction_index = prediction_indices["clean_prediction_index"]
    corrupted_prediction_index = prediction_indices["corrupted_prediction_index"]
    if target_layers is None:
        target_layers = select_top_layers_from_results(layer_results_path, example_id=example_id)
    target_layers = [int(layer_index) for layer_index in target_layers]

    runner = HeadPatchingPilotRunner(model_alias=model_alias)
    runner.load()

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
            + ". Rerun scripts/run_forward_pass_pilot.py before head patching."
        )

    token_info = {
        "hallucinated_token_id": int(artifact["hallucinated_token_id_at_divergence"]),
        "verified_truth_token_id": int(artifact["verified_truth_token_id_at_divergence"]),
        "hallucinated_token_text": artifact["hallucinated_token_text_at_divergence"],
        "verified_truth_token_text": artifact["verified_truth_token_text_at_divergence"],
    }

    clean_input_ids = artifact["clean"]["input_token_ids"].to(runner.device)
    corrupted_input_ids = artifact["corrupted"]["input_token_ids"].to(runner.device)
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

    donor_inputs = runner._capture_corrupted_head_inputs(
        corrupted_input_ids=corrupted_input_ids,
        target_layers=list(target_layers),
        corrupted_absolute_prediction_index=corrupted_prediction_index,
    )

    results: List[Dict[str, Any]] = []
    for layer_index in target_layers:
        donor_hidden = donor_inputs[layer_index]
        for head_index in range(runner.num_heads):
            patched_logits = runner._patch_single_head(
                layer_index=layer_index,
                head_index=head_index,
                clean_input_ids=clean_input_ids,
                clean_absolute_prediction_index=clean_prediction_index,
                donor_hidden=donor_hidden,
            )
            patched_target_logits = patched_logits[:, clean_prediction_index, :][0]

            patched_hallucinated_token_logit = float(
                patched_target_logits[token_info["hallucinated_token_id"]].item()
            )
            patched_verified_truth_token_logit = float(
                patched_target_logits[token_info["verified_truth_token_id"]].item()
            )
            patched_margin = patched_verified_truth_token_logit - patched_hallucinated_token_logit
            restoration_score = patched_margin - baseline_margin

            results.append(
                build_head_result_record(
                    example_id=example_id,
                    layer_index=layer_index,
                    head_index=head_index,
                    baseline_hallucinated_token_logit=baseline_hallucinated_token_logit,
                    baseline_verified_truth_token_logit=baseline_verified_truth_token_logit,
                    patched_hallucinated_token_logit=patched_hallucinated_token_logit,
                    patched_verified_truth_token_logit=patched_verified_truth_token_logit,
                    restoration_score=restoration_score,
                    hallucinated_token_id=token_info["hallucinated_token_id"],
                    verified_truth_token_id=token_info["verified_truth_token_id"],
                    hallucinated_token_text=token_info["hallucinated_token_text"],
                    verified_truth_token_text=token_info["verified_truth_token_text"],
                )
            )

    results.sort(key=lambda record: (record["layer_index"], record["head_index"]))
    write_results_jsonl(results, output_jsonl_path)

    top_heads_overall = sorted(results, key=lambda record: record["restoration_score"], reverse=True)[:10]
    top_heads_per_layer: Dict[str, List[Dict[str, Any]]] = {}
    for layer_index in target_layers:
        layer_records = [record for record in results if record["layer_index"] == layer_index]
        top_heads_per_layer[str(layer_index)] = sorted(
            layer_records, key=lambda record: record["restoration_score"], reverse=True
        )[:5]

    summary = {
        "example_id": example_id,
        "model_alias": model_alias,
        "target_layers": target_layers,
        "clean_absolute_divergence_prediction_index": clean_prediction_index,
        "corrupted_absolute_divergence_prediction_index": corrupted_prediction_index,
        "baseline_hallucinated_token_logit": baseline_hallucinated_token_logit,
        "baseline_verified_truth_token_logit": baseline_verified_truth_token_logit,
        "baseline_margin": baseline_margin,
        "top_heads_overall": top_heads_overall,
        "top_heads_per_layer": top_heads_per_layer,
    }
    write_head_patching_markdown(
        output_path=output_doc_path,
        summary=summary,
        input_pt_path=input_pt_path,
        output_jsonl_path=output_jsonl_path,
    )

    return {
        "results_path": output_jsonl_path,
        "doc_path": output_doc_path,
        "summary": summary,
    }
