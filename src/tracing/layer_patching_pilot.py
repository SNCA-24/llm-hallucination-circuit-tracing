import json
import os
from pathlib import Path
from typing import Any, Dict, List


SUPPORTED_MODEL_ALIASES = {
    "llama-2-7b-chat": "NousResearch/Llama-2-7b-chat-hf",
}


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


def load_tracing_metadata(metadata_path: str) -> Dict[str, Any]:
    return json.loads(Path(metadata_path).read_text(encoding="utf-8"))


def shape_to_list(shape: Any) -> List[int]:
    return [int(dim) for dim in tuple(shape)]


def _lazy_import_torch():
    try:
        import torch
    except ImportError as exc:
        raise ImportError(
            "Layer patching pilot requires 'torch'. Install it in Colab before running this script."
        ) from exc
    return torch


def load_forward_pass_artifact(input_path: str) -> Dict[str, Any]:
    torch = _lazy_import_torch()
    artifact = torch.load(input_path, map_location="cpu", weights_only=False)
    if artifact.get("model_alias") != "llama-2-7b-chat":
        raise ValueError("Layer patching pilot is locked to model_alias='llama-2-7b-chat'.")
    return artifact


def _require_int(value: Any, field_name: str) -> int:
    if value is None:
        raise ValueError(f"Forward-pass artifact is missing {field_name}.")
    return int(value)


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


def _require_model_alias(artifact: Dict[str, Any], model_alias: str) -> None:
    artifact_model_alias = artifact.get("model_alias")
    if artifact_model_alias != model_alias:
        raise ValueError(
            f"Forward-pass artifact model_alias must be {model_alias!r}; "
            f"got {artifact_model_alias!r}."
        )


def _require_prediction_indices(artifact: Dict[str, Any]) -> Dict[str, int]:
    clean = artifact.get("clean", {})
    corrupted = artifact.get("corrupted", {})
    clean_absolute_divergence_index = _require_int(
        clean.get("absolute_divergence_token_index"),
        "clean.absolute_divergence_token_index",
    )
    clean_absolute_divergence_prediction_index = _require_int(
        clean.get("absolute_divergence_prediction_index"),
        "clean.absolute_divergence_prediction_index",
    )
    corrupted_absolute_divergence_index = _require_int(
        corrupted.get("absolute_divergence_token_index"),
        "corrupted.absolute_divergence_token_index",
    )
    corrupted_absolute_divergence_prediction_index = _require_int(
        corrupted.get("absolute_divergence_prediction_index"),
        "corrupted.absolute_divergence_prediction_index",
    )

    if not clean.get("absolute_divergence_index_in_range"):
        raise ValueError("Clean absolute divergence token index is not marked in range.")
    if not corrupted.get("absolute_divergence_index_in_range"):
        raise ValueError("Corrupted absolute divergence token index is not marked in range.")
    if not clean.get("absolute_divergence_prediction_index_in_range"):
        raise ValueError("Clean absolute divergence prediction index is not marked in range.")
    if not corrupted.get("absolute_divergence_prediction_index_in_range"):
        raise ValueError("Corrupted absolute divergence prediction index is not marked in range.")

    clean_seq_len = int(clean["input_token_ids"].shape[1])
    corrupted_seq_len = int(corrupted["input_token_ids"].shape[1])
    if not 0 <= clean_absolute_divergence_prediction_index < clean_seq_len:
        raise ValueError(
            "Clean absolute divergence prediction index is outside the clean sequence: "
            f"{clean_absolute_divergence_prediction_index} not in [0, {clean_seq_len})."
        )
    if not 0 <= corrupted_absolute_divergence_prediction_index < corrupted_seq_len:
        raise ValueError(
            "Corrupted absolute divergence prediction index is outside the corrupted sequence: "
            f"{corrupted_absolute_divergence_prediction_index} not in [0, {corrupted_seq_len})."
        )
    if not 0 <= clean_absolute_divergence_index < clean_seq_len:
        raise ValueError(
            "Clean absolute divergence token index is outside the clean sequence: "
            f"{clean_absolute_divergence_index} not in [0, {clean_seq_len})."
        )
    if not 0 <= corrupted_absolute_divergence_index < corrupted_seq_len:
        raise ValueError(
            "Corrupted absolute divergence token index is outside the corrupted sequence: "
            f"{corrupted_absolute_divergence_index} not in [0, {corrupted_seq_len})."
        )

    return {
        "clean_absolute_divergence_index": clean_absolute_divergence_index,
        "clean_absolute_divergence_prediction_index": clean_absolute_divergence_prediction_index,
        "corrupted_absolute_divergence_index": corrupted_absolute_divergence_index,
        "corrupted_absolute_divergence_prediction_index": corrupted_absolute_divergence_prediction_index,
    }


def get_decoder_layers(model: Any) -> Any:
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        return model.model.layers
    if hasattr(model, "layers"):
        return model.layers
    raise AttributeError("Could not locate decoder layers on the loaded model.")


class LayerPatchingPilotRunner:
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

    def load(self) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "Layer patching pilot requires 'torch' and 'transformers'. "
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

    def _patch_layer_output(
        self,
        layer_index: int,
        clean_input_ids: Any,
        target_token_index: int,
        donor_hidden_state: Any,
    ) -> Any:
        decoder_layers = get_decoder_layers(self.model)
        attention_mask = self.torch.ones_like(clean_input_ids, device=self.device)
        donor_hidden_state = donor_hidden_state.to(device=self.device, dtype=self.model.dtype)

        def patch_hook(_module: Any, _inputs: Any, output: Any) -> Any:
            if isinstance(output, tuple):
                hidden_state = output[0].clone()
                hidden_state[:, target_token_index, :] = donor_hidden_state
                return (hidden_state,) + output[1:]

            hidden_state = output.clone()
            hidden_state[:, target_token_index, :] = donor_hidden_state
            return hidden_state

        hook = decoder_layers[layer_index].register_forward_hook(patch_hook)
        try:
            with self.torch.no_grad():
                outputs = self.model(
                    input_ids=clean_input_ids,
                    attention_mask=attention_mask,
                    return_dict=True,
                )
        finally:
            hook.remove()

        return outputs.logits.detach().cpu()


def build_layer_result_record(
    example_id: str,
    layer_index: int,
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


def write_layer_results_jsonl(results: List[Dict[str, Any]], output_path: str) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result) + "\n")


def write_layer_patching_markdown(
    output_path: str,
    summary: Dict[str, Any],
    input_path: str,
    output_jsonl_path: str,
) -> None:
    doc_path = Path(output_path)
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    top_layers = summary["top_layers"]

    with doc_path.open("w", encoding="utf-8") as handle:
        handle.write("# Layer Patching Pilot\n\n")
        handle.write("## Scope\n")
        handle.write(f"- Input artifact: `{input_path}`\n")
        handle.write(f"- Retained example ID: `{summary['example_id']}`\n")
        handle.write(f"- Model scope: `{summary['model_alias']}` only\n")
        handle.write("- Phase boundary: layer-level patching only; no head-wise patching or ablations yet\n\n")

        handle.write("## Baseline Target-Token Comparison\n")
        handle.write(
            f"- Output-relative divergence token index: "
            f"`{summary['output_relative_divergence_token_index']}`\n"
        )
        handle.write(
            f"- Clean absolute divergence token index: "
            f"`{summary['clean_absolute_divergence_token_index']}`\n"
        )
        handle.write(
            f"- Clean absolute divergence prediction index: "
            f"`{summary['clean_absolute_divergence_prediction_index']}`\n"
        )
        handle.write(
            f"- Corrupted absolute divergence token index: "
            f"`{summary['corrupted_absolute_divergence_token_index']}`\n"
        )
        handle.write(
            f"- Corrupted absolute divergence prediction index: "
            f"`{summary['corrupted_absolute_divergence_prediction_index']}`\n"
        )
        handle.write(
            f"- Hallucinated token at divergence: `{summary['hallucinated_token_text']}` "
            f"(id `{summary['hallucinated_token_id']}`)\n"
        )
        handle.write(
            f"- Verified-truth token at divergence: `{summary['verified_truth_token_text']}` "
            f"(id `{summary['verified_truth_token_id']}`)\n"
        )
        handle.write(
            f"- Baseline clean hallucinated-token logit: `{summary['baseline_hallucinated_token_logit']:.6f}`\n"
        )
        handle.write(
            f"- Baseline clean verified-truth-token logit: `{summary['baseline_verified_truth_token_logit']:.6f}`\n"
        )
        handle.write(
            f"- Baseline clean truth-minus-hallucination margin: "
            f"`{summary['baseline_margin']:.6f}`\n\n"
        )

        handle.write("## Top Restoring Layers\n")
        if not top_layers:
            handle.write("- No layer results were produced.\n\n")
        else:
            for record in top_layers:
                handle.write(
                    f"- Layer `{record['layer_index']}`: restoration score "
                    f"`{record['restoration_score']:.6f}`, patched truth logit "
                    f"`{record['patched_verified_truth_token_logit']:.6f}`, patched hallucinated logit "
                    f"`{record['patched_hallucinated_token_logit']:.6f}`\n"
                )
            handle.write("\n")

        handle.write("## Candidate Layers\n")
        if top_layers:
            strongest = ", ".join(str(record["layer_index"]) for record in top_layers[:3])
            handle.write(
                f"- Strongest candidate restoring layers from this single-pair pilot: `{strongest}`\n\n"
            )
        else:
            handle.write("- No candidate layers identified.\n\n")

        handle.write("## Output Artifact\n")
        handle.write(f"- Layer results JSONL: `{output_jsonl_path}`\n")


def run_layer_patching_pilot(
    input_pt_path: str = "outputs/forward_pass_pilot.pt",
    metadata_path: str = "outputs/tracing_pilot_input.json",
    output_jsonl_path: str = "outputs/layer_patching_results.jsonl",
    output_doc_path: str = "docs/layer_patching_pilot.md",
    model_alias: str = "llama-2-7b-chat",
) -> Dict[str, Any]:
    artifact = load_forward_pass_artifact(input_pt_path)
    metadata = load_tracing_metadata(metadata_path)

    example_id = _require_matching_example_ids(artifact, metadata)
    _require_model_alias(artifact, model_alias)

    output_relative_divergence_index = _require_int(
        artifact.get("output_relative_divergence_token_index"),
        "output_relative_divergence_token_index",
    )
    prediction_indices = _require_prediction_indices(artifact)
    clean_absolute_divergence_index = prediction_indices["clean_absolute_divergence_index"]
    clean_absolute_divergence_prediction_index = prediction_indices[
        "clean_absolute_divergence_prediction_index"
    ]
    corrupted_absolute_divergence_index = prediction_indices["corrupted_absolute_divergence_index"]
    corrupted_absolute_divergence_prediction_index = prediction_indices[
        "corrupted_absolute_divergence_prediction_index"
    ]

    runner = LayerPatchingPilotRunner(model_alias=model_alias)
    runner.load()
    token_info = {
        "hallucinated_token_id": int(metadata["hallucinated_token_id_at_divergence"]),
        "verified_truth_token_id": int(metadata["verified_truth_token_id_at_divergence"]),
        "hallucinated_token_text": metadata["hallucinated_token_text_at_divergence"],
        "verified_truth_token_text": metadata["verified_truth_token_text_at_divergence"],
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

    corrupted_hidden_states = artifact["corrupted"]["hidden_states"]
    clean_hidden_states = artifact["clean"]["hidden_states"]
    if len(corrupted_hidden_states) != len(clean_hidden_states):
        raise ValueError("Clean/corrupted hidden-state layer counts do not match.")

    num_decoder_layers = len(corrupted_hidden_states) - 1
    results: List[Dict[str, Any]] = []

    for layer_index in range(num_decoder_layers):
        donor_hidden_state = corrupted_hidden_states[layer_index + 1][
            :, corrupted_absolute_divergence_prediction_index, :
        ]
        patched_logits = runner._patch_layer_output(
            layer_index=layer_index,
            clean_input_ids=clean_input_ids,
            target_token_index=clean_absolute_divergence_prediction_index,
            donor_hidden_state=donor_hidden_state,
        )
        patched_target_logits = patched_logits[:, clean_absolute_divergence_prediction_index, :][0]

        patched_hallucinated_token_logit = float(
            patched_target_logits[token_info["hallucinated_token_id"]].item()
        )
        patched_verified_truth_token_logit = float(
            patched_target_logits[token_info["verified_truth_token_id"]].item()
        )
        patched_margin = patched_verified_truth_token_logit - patched_hallucinated_token_logit
        restoration_score = patched_margin - baseline_margin

        results.append(
            build_layer_result_record(
                example_id=example_id,
                layer_index=layer_index,
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

    results.sort(key=lambda record: record["layer_index"])
    write_layer_results_jsonl(results, output_jsonl_path)

    top_layers = sorted(results, key=lambda record: record["restoration_score"], reverse=True)[:5]
    summary = {
        "example_id": example_id,
        "model_alias": model_alias,
        "target_token_index": output_relative_divergence_index,
        "output_relative_divergence_token_index": output_relative_divergence_index,
        "clean_absolute_divergence_token_index": clean_absolute_divergence_index,
        "clean_absolute_divergence_prediction_index": clean_absolute_divergence_prediction_index,
        "corrupted_absolute_divergence_token_index": corrupted_absolute_divergence_index,
        "corrupted_absolute_divergence_prediction_index": corrupted_absolute_divergence_prediction_index,
        "hallucinated_token_id": token_info["hallucinated_token_id"],
        "verified_truth_token_id": token_info["verified_truth_token_id"],
        "hallucinated_token_text": token_info["hallucinated_token_text"],
        "verified_truth_token_text": token_info["verified_truth_token_text"],
        "baseline_hallucinated_token_logit": baseline_hallucinated_token_logit,
        "baseline_verified_truth_token_logit": baseline_verified_truth_token_logit,
        "baseline_margin": baseline_margin,
        "top_layers": top_layers,
    }
    write_layer_patching_markdown(
        output_path=output_doc_path,
        summary=summary,
        input_path=input_pt_path,
        output_jsonl_path=output_jsonl_path,
    )

    return {
        "results_path": output_jsonl_path,
        "doc_path": output_doc_path,
        "summary": summary,
    }
