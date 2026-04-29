import json
import os
from pathlib import Path
from typing import Any, Dict, List


SUPPORTED_MODEL_ALIASES = {
    "llama-2-7b-chat": "NousResearch/Llama-2-7b-chat-hf",
}

REQUIRED_TRACING_INPUT_FIELDS = (
    "example_id",
    "built_clean_prompt",
    "built_corrupted_prompt",
    "model_output_clean",
    "model_output_corrupted",
)


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


def load_tracing_pilot_input(input_path: str) -> Dict[str, Any]:
    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    missing_fields = [
        field_name
        for field_name in REQUIRED_TRACING_INPUT_FIELDS
        if not str(payload.get(field_name, "")).strip()
    ]
    if missing_fields:
        raise ValueError(
            "Tracing input is missing required field(s): "
            + ", ".join(missing_fields)
        )
    return payload


class ForwardPassPilotRunner:
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
                "Forward-pass tracing pilot requires 'torch' and 'transformers'. "
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

    def _tensor_to_cpu(self, tensor: Any) -> Any:
        return tensor.detach().cpu()

    def _decode_tokens(self, input_ids: Any) -> List[str]:
        return [self.tokenizer.decode([token_id]) for token_id in input_ids[0].tolist()]

    def encode_text(self, text: str) -> Any:
        encoded = self.tokenizer(text, return_tensors="pt", add_special_tokens=False)
        return encoded["input_ids"][0]

    def token_id_to_text(self, token_id: int) -> str:
        return self.tokenizer.decode([int(token_id)])

    def build_teacher_forced_sequence(self, prompt_text: str, output_text: str) -> Dict[str, Any]:
        prompt_ids = self.encode_text(prompt_text)
        full_ids = self.encode_text(prompt_text + output_text)
        prompt_length = int(prompt_ids.shape[0])
        total_length = int(full_ids.shape[0])
        output_ids = full_ids[prompt_length:]
        output_length = int(output_ids.shape[0])
        if output_length <= 0:
            raise ValueError("Teacher-forced sequence has zero output tokens.")

        return {
            "prompt_token_ids": prompt_ids,
            "output_token_ids": output_ids,
            "full_token_ids": full_ids,
            "prompt_length_tokens": prompt_length,
            "output_length_tokens": output_length,
            "total_sequence_length_tokens": total_length,
        }

    def compute_validated_divergence(
        self,
        clean_prompt_text: str,
        clean_output_text: str,
        corrupted_prompt_text: str,
        corrupted_output_text: str,
    ) -> Dict[str, Any]:
        clean_sequence = self.build_teacher_forced_sequence(clean_prompt_text, clean_output_text)
        corrupted_sequence = self.build_teacher_forced_sequence(corrupted_prompt_text, corrupted_output_text)

        clean_output_ids = clean_sequence["output_token_ids"]
        corrupted_output_ids = corrupted_sequence["output_token_ids"]
        min_len = min(int(clean_output_ids.shape[0]), int(corrupted_output_ids.shape[0]))
        divergence_index = None
        for idx in range(min_len):
            if int(clean_output_ids[idx].item()) != int(corrupted_output_ids[idx].item()):
                divergence_index = idx
                break

        if divergence_index is None:
            if int(clean_output_ids.shape[0]) == int(corrupted_output_ids.shape[0]):
                raise ValueError("Validated outputs are identical under tokenizer; no divergent token found.")
            divergence_index = min_len

        if divergence_index >= int(clean_output_ids.shape[0]) or divergence_index >= int(corrupted_output_ids.shape[0]):
            raise ValueError(
                "First divergent token falls beyond one tokenized output. "
                "Current pilot requires an in-range divergence index for both runs."
            )

        hallucinated_token_id = int(clean_output_ids[divergence_index].item())
        verified_truth_token_id = int(corrupted_output_ids[divergence_index].item())
        clean_absolute_divergence_index = clean_sequence["prompt_length_tokens"] + divergence_index
        corrupted_absolute_divergence_index = corrupted_sequence["prompt_length_tokens"] + divergence_index

        return {
            "validated_divergence_token_index": divergence_index,
            "output_relative_divergence_token_index": divergence_index,
            "clean_absolute_divergence_token_index": clean_absolute_divergence_index,
            "corrupted_absolute_divergence_token_index": corrupted_absolute_divergence_index,
            "hallucinated_token_id_at_divergence": hallucinated_token_id,
            "verified_truth_token_id_at_divergence": verified_truth_token_id,
            "hallucinated_token_text_at_divergence": self.token_id_to_text(hallucinated_token_id),
            "verified_truth_token_text_at_divergence": self.token_id_to_text(verified_truth_token_id),
            "clean_prompt_length_tokens": clean_sequence["prompt_length_tokens"],
            "clean_output_length_tokens": clean_sequence["output_length_tokens"],
            "clean_total_sequence_length_tokens": clean_sequence["total_sequence_length_tokens"],
            "corrupted_prompt_length_tokens": corrupted_sequence["prompt_length_tokens"],
            "corrupted_output_length_tokens": corrupted_sequence["output_length_tokens"],
            "corrupted_total_sequence_length_tokens": corrupted_sequence["total_sequence_length_tokens"],
        }

    def forward_teacher_forced_sequence(
        self,
        prompt_text: str,
        output_text: str,
        output_relative_divergence_index: int,
    ) -> Dict[str, Any]:
        sequence_info = self.build_teacher_forced_sequence(prompt_text, output_text)
        full_token_ids = sequence_info["full_token_ids"]
        input_ids = full_token_ids.unsqueeze(0).to(self.device)
        attention_mask = self.torch.ones_like(input_ids, device=self.device)
        absolute_divergence_index = sequence_info["prompt_length_tokens"] + output_relative_divergence_index
        absolute_divergence_prediction_index = absolute_divergence_index - 1

        with self.torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=True,
                return_dict=True,
            )

        input_ids_cpu = self._tensor_to_cpu(input_ids)
        logits_cpu = self._tensor_to_cpu(outputs.logits)
        hidden_states_cpu = tuple(self._tensor_to_cpu(state) for state in outputs.hidden_states)
        seq_len = int(input_ids_cpu.shape[1])
        absolute_divergence_in_range = 0 <= absolute_divergence_index < seq_len
        absolute_divergence_prediction_index_in_range = (
            0 <= absolute_divergence_prediction_index < seq_len
        )

        target_logits = None
        if absolute_divergence_prediction_index_in_range:
            target_logits = logits_cpu[:, absolute_divergence_prediction_index, :]

        return {
            "input_token_ids": input_ids_cpu,
            "decoded_tokens": self._decode_tokens(input_ids_cpu),
            "full_output_logits": logits_cpu,
            "hidden_states": hidden_states_cpu,
            "output_relative_divergence_token_index": output_relative_divergence_index,
            "absolute_divergence_token_index": absolute_divergence_index,
            "absolute_divergence_prediction_index": absolute_divergence_prediction_index,
            "absolute_divergence_index_in_range": absolute_divergence_in_range,
            "absolute_divergence_prediction_index_in_range": absolute_divergence_prediction_index_in_range,
            "logits_at_absolute_divergence_prediction_position": target_logits,
            "prompt_length_tokens": sequence_info["prompt_length_tokens"],
            "output_length_tokens": sequence_info["output_length_tokens"],
            "total_sequence_length_tokens": sequence_info["total_sequence_length_tokens"],
        }


def shape_to_list(shape: Any) -> List[int]:
    return [int(dim) for dim in tuple(shape)]


def hidden_state_shapes(hidden_states: Any) -> List[List[int]]:
    return [shape_to_list(state.shape) for state in hidden_states]


def update_tracing_pilot_input(input_path: str, payload: Dict[str, Any], divergence_info: Dict[str, Any]) -> None:
    updated_payload = dict(payload)
    updated_payload.update(divergence_info)
    Path(input_path).write_text(json.dumps(updated_payload, indent=2) + "\n", encoding="utf-8")


def write_forward_pass_markdown(
    summary: Dict[str, Any],
    output_path: str,
    input_path: str,
    output_tensor_path: str,
) -> None:
    doc_path = Path(output_path)
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    with doc_path.open("w", encoding="utf-8") as handle:
        handle.write("# Forward Pass Pilot\n\n")
        handle.write("## Scope\n")
        handle.write(f"- Input file: `{input_path}`\n")
        handle.write(f"- Model scope: `{summary['model_alias']}` only\n")
        handle.write("- Phase boundary: forward-pass caching only; no activation patching or head-wise tracing yet\n\n")

        handle.write("## Runtime Summary\n")
        handle.write(f"- Example ID: `{summary['example_id']}`\n")
        handle.write(
            f"- Output-relative divergence token index: "
            f"`{summary['output_relative_divergence_token_index']}`\n"
        )
        handle.write(
            f"- Clean absolute divergence token index: "
            f"`{summary['clean']['absolute_divergence_token_index']}`\n"
        )
        handle.write(
            f"- Clean absolute divergence prediction index: "
            f"`{summary['clean']['absolute_divergence_prediction_index']}`\n"
        )
        handle.write(
            f"- Corrupted absolute divergence token index: "
            f"`{summary['corrupted']['absolute_divergence_token_index']}`\n"
        )
        handle.write(
            f"- Corrupted absolute divergence prediction index: "
            f"`{summary['corrupted']['absolute_divergence_prediction_index']}`\n"
        )
        handle.write(
            f"- Hallucinated token at divergence: `{summary['hallucinated_token_text_at_divergence']}` "
            f"(id `{summary['hallucinated_token_id_at_divergence']}`)\n"
        )
        handle.write(
            f"- Verified-truth token at divergence: `{summary['verified_truth_token_text_at_divergence']}` "
            f"(id `{summary['verified_truth_token_id_at_divergence']}`)\n"
        )
        handle.write(
            f"- Clean divergence index in range: "
            f"`{summary['clean']['absolute_divergence_index_in_range']}`\n"
        )
        handle.write(
            f"- Clean prediction index in range: "
            f"`{summary['clean']['absolute_divergence_prediction_index_in_range']}`\n"
        )
        handle.write(
            f"- Corrupted divergence index in range: "
            f"`{summary['corrupted']['absolute_divergence_index_in_range']}`\n"
        )
        handle.write(
            f"- Corrupted prediction index in range: "
            f"`{summary['corrupted']['absolute_divergence_prediction_index_in_range']}`\n\n"
        )

        handle.write("## Prompt Summary\n")
        handle.write(f"- Clean prompt length (tokens): `{summary['clean']['prompt_length_tokens']}`\n")
        handle.write(f"- Clean output length (tokens): `{summary['clean']['output_length_tokens']}`\n")
        handle.write(f"- Clean total sequence length (tokens): `{summary['clean']['total_sequence_length_tokens']}`\n")
        handle.write(f"- Corrupted prompt length (tokens): `{summary['corrupted']['prompt_length_tokens']}`\n")
        handle.write(f"- Corrupted output length (tokens): `{summary['corrupted']['output_length_tokens']}`\n")
        handle.write(f"- Corrupted total sequence length (tokens): `{summary['corrupted']['total_sequence_length_tokens']}`\n")
        handle.write("\n")

        handle.write("## Tensor Shapes\n")
        handle.write(
            f"- Clean logits shape: `{summary['clean']['full_output_logits_shape']}`\n"
        )
        handle.write(
            f"- Corrupted logits shape: `{summary['corrupted']['full_output_logits_shape']}`\n"
        )
        handle.write(
            f"- Clean hidden-state count: `{summary['clean']['hidden_state_count']}`\n"
        )
        handle.write(
            f"- Corrupted hidden-state count: `{summary['corrupted']['hidden_state_count']}`\n"
        )
        handle.write(
            f"- Clean hidden-state shapes: `{summary['clean']['hidden_state_shapes']}`\n"
        )
        handle.write(
            f"- Corrupted hidden-state shapes: `{summary['corrupted']['hidden_state_shapes']}`\n"
        )
        handle.write(
            f"- Clean divergence-prediction logits shape: `{summary['clean']['target_logits_shape']}`\n"
        )
        handle.write(
            f"- Corrupted divergence-prediction logits shape: `{summary['corrupted']['target_logits_shape']}`\n\n"
        )

        handle.write("## Output Artifact\n")
        handle.write(f"- Tensor export: `{output_tensor_path}`\n")


def run_forward_pass_pilot(
    input_path: str = "outputs/tracing_pilot_input.json",
    output_tensor_path: str = "outputs/forward_pass_pilot.pt",
    output_doc_path: str = "docs/forward_pass_pilot.md",
    model_alias: str = "llama-2-7b-chat",
    update_input_with_divergence: bool = True,
    updated_input_output_path: str | None = None,
) -> Dict[str, Any]:
    payload = load_tracing_pilot_input(input_path)

    runner = ForwardPassPilotRunner(model_alias=model_alias)
    runner.load()

    divergence_info = runner.compute_validated_divergence(
        clean_prompt_text=payload["built_clean_prompt"],
        clean_output_text=payload["model_output_clean"],
        corrupted_prompt_text=payload["built_corrupted_prompt"],
        corrupted_output_text=payload["model_output_corrupted"],
    )
    if update_input_with_divergence:
        update_tracing_pilot_input(input_path=input_path, payload=payload, divergence_info=divergence_info)
    if updated_input_output_path:
        update_tracing_pilot_input(
            input_path=updated_input_output_path,
            payload=payload,
            divergence_info=divergence_info,
        )
    target_token_index = int(divergence_info["output_relative_divergence_token_index"])

    clean_result = runner.forward_teacher_forced_sequence(
        prompt_text=payload["built_clean_prompt"],
        output_text=payload["model_output_clean"],
        output_relative_divergence_index=target_token_index,
    )
    corrupted_result = runner.forward_teacher_forced_sequence(
        prompt_text=payload["built_corrupted_prompt"],
        output_text=payload["model_output_corrupted"],
        output_relative_divergence_index=target_token_index,
    )

    export_payload = {
        "example_id": payload["example_id"],
        "model_alias": model_alias,
        "model_name": runner.model_name,
        "target_token_index": target_token_index,
        **divergence_info,
        "clean": clean_result,
        "corrupted": corrupted_result,
    }

    tensor_path = Path(output_tensor_path)
    tensor_path.parent.mkdir(parents=True, exist_ok=True)
    runner.torch.save(export_payload, tensor_path)

    summary = {
        "example_id": payload["example_id"],
        "model_alias": model_alias,
        "target_token_index": target_token_index,
        "output_relative_divergence_token_index": target_token_index,
        **divergence_info,
        "clean": {
            "prompt_length_tokens": clean_result["prompt_length_tokens"],
            "output_length_tokens": clean_result["output_length_tokens"],
            "total_sequence_length_tokens": clean_result["total_sequence_length_tokens"],
            "absolute_divergence_token_index": clean_result["absolute_divergence_token_index"],
            "absolute_divergence_prediction_index": clean_result["absolute_divergence_prediction_index"],
            "absolute_divergence_index_in_range": clean_result["absolute_divergence_index_in_range"],
            "absolute_divergence_prediction_index_in_range": clean_result["absolute_divergence_prediction_index_in_range"],
            "full_output_logits_shape": shape_to_list(clean_result["full_output_logits"].shape),
            "hidden_state_count": len(clean_result["hidden_states"]),
            "hidden_state_shapes": hidden_state_shapes(clean_result["hidden_states"]),
            "target_logits_shape": (
                None
                if clean_result["logits_at_absolute_divergence_prediction_position"] is None
                else shape_to_list(clean_result["logits_at_absolute_divergence_prediction_position"].shape)
            ),
        },
        "corrupted": {
            "prompt_length_tokens": corrupted_result["prompt_length_tokens"],
            "output_length_tokens": corrupted_result["output_length_tokens"],
            "total_sequence_length_tokens": corrupted_result["total_sequence_length_tokens"],
            "absolute_divergence_token_index": corrupted_result["absolute_divergence_token_index"],
            "absolute_divergence_prediction_index": corrupted_result["absolute_divergence_prediction_index"],
            "absolute_divergence_index_in_range": corrupted_result["absolute_divergence_index_in_range"],
            "absolute_divergence_prediction_index_in_range": corrupted_result["absolute_divergence_prediction_index_in_range"],
            "full_output_logits_shape": shape_to_list(corrupted_result["full_output_logits"].shape),
            "hidden_state_count": len(corrupted_result["hidden_states"]),
            "hidden_state_shapes": hidden_state_shapes(corrupted_result["hidden_states"]),
            "target_logits_shape": (
                None
                if corrupted_result["logits_at_absolute_divergence_prediction_position"] is None
                else shape_to_list(corrupted_result["logits_at_absolute_divergence_prediction_position"].shape)
            ),
        },
    }

    write_forward_pass_markdown(
        summary=summary,
        output_path=output_doc_path,
        input_path=input_path,
        output_tensor_path=output_tensor_path,
    )

    return {
        "tensor_output_path": str(tensor_path),
        "doc_output_path": output_doc_path,
        "summary": summary,
    }
