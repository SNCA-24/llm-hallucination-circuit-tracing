import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

SUPPORTED_MODEL_ALIASES = {
    "llama-2-7b-chat": "NousResearch/Llama-2-7b-chat-hf",
}

REQUIRED_CSV_FIELDS = (
    "ground_truth_text_verified",
    "corrupted_prompt_candidate",
    "edit_class",
)


def _is_non_empty(value: str) -> bool:
    return bool((value or "").strip())


def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).casefold()


def contains_normalized_substring(haystack: str, needle: str) -> bool:
    if not _is_non_empty(needle):
        return False
    return _normalize_for_match(needle) in _normalize_for_match(haystack)


def strip_trailing_output_marker(text: str) -> str:
    return re.sub(r"(?:\n\s*)?output\s*:\s*$", "", (text or ""), flags=re.IGNORECASE).strip()


def remove_context_from_prompt(prompt_text: str, context_text: str) -> str:
    prompt_text = prompt_text or ""
    context_text = context_text or ""
    if context_text and context_text in prompt_text:
        prompt_text = prompt_text.replace(context_text, "", 1)
    return prompt_text.strip()


def build_llama2_chat_prompt(prompt_text: str, raw_source_info_field: str) -> Dict[str, str]:
    context = (raw_source_info_field or "").strip()
    query = remove_context_from_prompt(prompt_text, context)
    query = strip_trailing_output_marker(query)

    if context:
        prompt_core = f"{query}\n\n{context}" if query else context
    else:
        prompt_core = query

    full_prompt = f"<s>[INST] {prompt_core} [/INST]"
    return {
        "query": query,
        "context": context,
        "full_prompt": full_prompt,
    }


@dataclass
class PairValidationInput:
    example_id: str
    edit_class: str
    hallucinated_substring: str
    clean_input_text_for_validation: str
    corrupted_prompt_candidate: str
    ground_truth_text_verified: str
    raw_prompt_field: str
    raw_source_info_field: str

    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> "PairValidationInput":
        return cls(
            example_id=str(row.get("example_id", "")).strip(),
            edit_class=(row.get("edit_class") or "").strip(),
            hallucinated_substring=(row.get("hallucinated_substring") or "").strip(),
            clean_input_text_for_validation=(row.get("clean_input_text_for_validation") or "").strip(),
            corrupted_prompt_candidate=(row.get("corrupted_prompt_candidate") or "").strip(),
            ground_truth_text_verified=(row.get("ground_truth_text_verified") or "").strip(),
            raw_prompt_field=(row.get("raw_prompt_field") or "").strip(),
            raw_source_info_field=(row.get("raw_source_info_field") or "").strip(),
        )

    def teacher_forcing_stub(self) -> Dict[str, Any]:
        # Placeholder payload shape for a later teacher-forcing scorer.
        return {
            "example_id": self.example_id,
            "clean_prompt": self.clean_input_text_for_validation,
            "corrupted_prompt": self.corrupted_prompt_candidate,
            "expected_truth_text": self.ground_truth_text_verified,
            "target_hallucinated_substring": self.hallucinated_substring,
        }


def load_pair_validation_inputs(
    csv_path: str,
    allowed_example_ids: Sequence[str],
) -> Tuple[List[PairValidationInput], List[Dict[str, str]]]:
    allowed_ids = {str(example_id) for example_id in allowed_example_ids}
    allowed_order = {str(example_id): index for index, example_id in enumerate(allowed_example_ids)}
    kept_rows: List[PairValidationInput] = []
    skipped_rows: List[Dict[str, str]] = []

    with open(csv_path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            example_id = str(row.get("example_id", "")).strip()
            if example_id not in allowed_ids:
                continue

            missing_fields = [
                field_name
                for field_name in REQUIRED_CSV_FIELDS
                if not _is_non_empty(row.get(field_name, ""))
            ]
            if not _is_non_empty(row.get("clean_input_text_for_validation", "")):
                missing_fields.append("clean_input_text_for_validation")

            if missing_fields:
                skipped_rows.append(
                    {
                        "example_id": example_id,
                        "reason": f"missing required field(s): {', '.join(sorted(set(missing_fields)))}",
                    }
                )
                continue

            kept_rows.append(PairValidationInput.from_csv_row(row))

    kept_rows.sort(key=lambda item: allowed_order[item.example_id])
    skipped_rows.sort(key=lambda item: allowed_order[item["example_id"]])
    return kept_rows, skipped_rows


def load_pair_validation_inputs_from_registry_rows(
    rows: Sequence[Dict[str, str]],
    allowed_example_ids: Sequence[str],
) -> Tuple[List[PairValidationInput], List[Dict[str, str]]]:
    allowed_order = {str(example_id): index for index, example_id in enumerate(allowed_example_ids)}
    kept_rows: List[PairValidationInput] = []
    skipped_rows: List[Dict[str, str]] = []

    for row in rows:
        example_id = str(row.get("example_id", "")).strip()
        missing_fields = [
            field_name
            for field_name in REQUIRED_CSV_FIELDS
            if not _is_non_empty(row.get(field_name, ""))
        ]
        if not _is_non_empty(row.get("clean_input_text_for_validation", "")):
            missing_fields.append("clean_input_text_for_validation")

        if missing_fields:
            skipped_rows.append(
                {
                    "example_id": example_id,
                    "reason": f"missing required field(s): {', '.join(sorted(set(missing_fields)))}",
                }
            )
            continue

        kept_rows.append(PairValidationInput.from_csv_row(row))

    kept_rows.sort(key=lambda item: allowed_order.get(item.example_id, len(allowed_order)))
    skipped_rows.sort(key=lambda item: allowed_order.get(item["example_id"], len(allowed_order)))
    return kept_rows, skipped_rows


def validation_passed(result: Dict[str, Any]) -> bool:
    return (
        result.get("clean_reproduction_status") == "reproduced_hallucination"
        and result.get("corrupted_flip_status") == "flipped_to_verified_truth"
    )


class LlamaPairValidator:
    def __init__(self, model_alias: str, generation_settings: Dict[str, Any]):
        if model_alias not in SUPPORTED_MODEL_ALIASES:
            raise ValueError(
                f"Unsupported model alias '{model_alias}'. "
                f"Supported aliases: {sorted(SUPPORTED_MODEL_ALIASES)}"
            )

        self.model_alias = model_alias
        self.model_name = SUPPORTED_MODEL_ALIASES[model_alias]
        self.generation_settings = dict(generation_settings)
        self.device = None
        self.torch = None
        self.auto_model_cls = None
        self.auto_tokenizer_cls = None
        self.tokenizer = None
        self.model = None

    def load(self) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
        except ImportError as exc:
            raise ImportError(
                "Pair validation requires 'torch' and 'transformers'. "
                "Install them in Colab before running this script."
            ) from exc

        self.torch = torch
        self.auto_model_cls = AutoModelForCausalLM
        self.auto_tokenizer_cls = AutoTokenizer
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        set_seed(int(self.generation_settings.get("seed", 42)))
        self.tokenizer = self.auto_tokenizer_cls.from_pretrained(self.model_name, use_fast=True)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        model_kwargs: Dict[str, Any] = {"low_cpu_mem_usage": True}
        if self.device == "cuda":
            model_kwargs["torch_dtype"] = torch.float16

        self.model = self.auto_model_cls.from_pretrained(self.model_name, **model_kwargs)
        self.model.to(self.device)
        self.model.eval()

    def _build_generate_kwargs(self) -> Dict[str, Any]:
        do_sample = bool(self.generation_settings.get("do_sample", False))
        kwargs: Dict[str, Any] = {
            "max_new_tokens": int(self.generation_settings.get("max_new_tokens", 96)),
            "do_sample": do_sample,
            "repetition_penalty": float(self.generation_settings.get("repetition_penalty", 1.0)),
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
        }
        if do_sample:
            kwargs["temperature"] = float(self.generation_settings.get("temperature", 1.0))
            kwargs["top_p"] = float(self.generation_settings.get("top_p", 1.0))
        return kwargs

    def generate(self, prompt: str) -> str:
        encoded_inputs = self.tokenizer(prompt, return_tensors="pt")
        encoded_inputs = {key: value.to(self.device) for key, value in encoded_inputs.items()}
        prompt_length = encoded_inputs["input_ids"].shape[1]

        with self.torch.no_grad():
            generated_ids = self.model.generate(**encoded_inputs, **self._build_generate_kwargs())

        new_token_ids = generated_ids[0][prompt_length:]
        return self.tokenizer.decode(new_token_ids, skip_special_tokens=True).strip()

    def validate_pair(self, row: PairValidationInput) -> Dict[str, Any]:
        clean_prompt_parts = build_llama2_chat_prompt(
            prompt_text=row.raw_prompt_field or row.clean_input_text_for_validation,
            raw_source_info_field=row.raw_source_info_field,
        )
        corrupted_prompt_parts = build_llama2_chat_prompt(
            prompt_text=row.corrupted_prompt_candidate,
            raw_source_info_field=row.raw_source_info_field,
        )

        clean_output = self.generate(clean_prompt_parts["full_prompt"])
        corrupted_output = self.generate(corrupted_prompt_parts["full_prompt"])

        clean_contains_hallucination = contains_normalized_substring(
            clean_output,
            row.hallucinated_substring,
        )
        corrupted_contains_truth = contains_normalized_substring(
            corrupted_output,
            row.ground_truth_text_verified,
        )
        corrupted_contains_hallucination = contains_normalized_substring(
            corrupted_output,
            row.hallucinated_substring,
        )

        if clean_contains_hallucination:
            clean_reproduction_status = "reproduced_hallucination"
        else:
            clean_reproduction_status = "not_reproduced"

        if corrupted_contains_truth and not corrupted_contains_hallucination:
            corrupted_flip_status = "flipped_to_verified_truth"
        elif corrupted_contains_truth and corrupted_contains_hallucination:
            corrupted_flip_status = "truth_present_but_hallucination_still_present"
        else:
            corrupted_flip_status = "did_not_flip"

        return {
            "example_id": row.example_id,
            "model_alias": self.model_alias,
            "model_name": self.model_name,
            "edit_class": row.edit_class,
            "hallucinated_substring": row.hallucinated_substring,
            "verified_truth_text": row.ground_truth_text_verified,
            "clean_reproduction_status": clean_reproduction_status,
            "corrupted_flip_status": corrupted_flip_status,
            "built_clean_prompt": clean_prompt_parts["full_prompt"],
            "built_corrupted_prompt": corrupted_prompt_parts["full_prompt"],
            "model_output_clean": clean_output,
            "model_output_corrupted": corrupted_output,
            "verified_truth_appears_in_corrupted_output": corrupted_contains_truth,
            "clean_contains_hallucinated_substring": clean_contains_hallucination,
            "corrupted_contains_hallucinated_substring": corrupted_contains_hallucination,
            "generation_settings_used": dict(self.generation_settings),
            "teacher_forcing_stub": row.teacher_forcing_stub(),
        }


def write_results_jsonl(results: Sequence[Dict[str, Any]], output_path: str) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result) + "\n")


def write_validation_markdown(
    results: Sequence[Dict[str, Any]],
    skipped_rows: Sequence[Dict[str, str]],
    output_path: str,
    input_csv_path: str,
    model_alias: str,
    generation_settings: Dict[str, Any],
    target_example_ids: Sequence[str],
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as handle:
        handle.write("# Pair Validation\n\n")
        handle.write("## Scope\n")
        handle.write(f"- Input CSV: `{input_csv_path}`\n")
        handle.write(
            "- Allowed example IDs: "
            + ", ".join(f"`{example_id}`" for example_id in target_example_ids)
            + "\n"
        )
        handle.write(f"- Model scope: `{model_alias}` only\n")
        handle.write("- Phase boundary: pair validation only; no tracing implemented here\n\n")

        handle.write("## Generation Settings\n")
        for key, value in generation_settings.items():
            handle.write(f"- `{key}`: `{value}`\n")
        handle.write("\n")

        handle.write("## Input Filtering\n")
        handle.write(f"- Eligible rows run: {len(results)}\n")
        handle.write(f"- Eligible rows skipped: {len(skipped_rows)}\n")
        for skipped in skipped_rows:
            handle.write(
                f"- Skipped example `{skipped['example_id']}`: {skipped['reason']}\n"
            )
        handle.write("\n")

        handle.write("## Per-Example Results\n")
        if not results:
            handle.write("- No eligible rows were available for validation.\n")
            return

        for result in results:
            handle.write(f"### Example {result['example_id']}\n")
            handle.write(
                f"- Clean reproduction status: `{result['clean_reproduction_status']}`\n"
            )
            handle.write(
                f"- Corrupted flip status: `{result['corrupted_flip_status']}`\n"
            )
            handle.write(
                "- Verified truth appears in corrupted output: "
                f"`{result['verified_truth_appears_in_corrupted_output']}`\n"
            )
            handle.write(
                "- Clean output contains hallucinated substring: "
                f"`{result['clean_contains_hallucinated_substring']}`\n"
            )
            handle.write(
                "- Corrupted output contains hallucinated substring: "
                f"`{result['corrupted_contains_hallucinated_substring']}`\n"
            )
            handle.write(f"- Clean output: `{result['model_output_clean']}`\n")
            handle.write(f"- Corrupted output: `{result['model_output_corrupted']}`\n\n")


def run_pair_validation(config: Any) -> Dict[str, Any]:
    if config.primary_model != "llama-2-7b-chat":
        raise ValueError(
            "Pair validation is currently locked to primary_model='llama-2-7b-chat'."
        )

    generation_settings = dict(config.generation_settings or {})
    if not generation_settings:
        raise ValueError("generation_settings are missing from the config.")

    pair_validation_config = dict(config.pair_validation or {})
    input_csv_path = pair_validation_config.get(
        "input_csv",
        "outputs/pair_authoring_review_sheet.csv",
    )
    target_example_ids = pair_validation_config.get("target_example_ids", ["51", "369"])
    results_output_path = config.output_paths.get(
        "pair_validation_results",
        "outputs/pair_validation_results.jsonl",
    )
    doc_output_path = config.output_paths.get(
        "pair_validation_doc",
        "docs/pair_validation.md",
    )

    rows_to_run, skipped_rows = load_pair_validation_inputs(
        csv_path=input_csv_path,
        allowed_example_ids=target_example_ids,
    )

    if not rows_to_run:
        write_results_jsonl([], results_output_path)
        write_validation_markdown(
            results=[],
            skipped_rows=skipped_rows,
            output_path=doc_output_path,
            input_csv_path=input_csv_path,
            model_alias=config.primary_model,
            generation_settings=generation_settings,
            target_example_ids=target_example_ids,
        )
        return {
            "rows_run": 0,
            "results_output_path": results_output_path,
            "doc_output_path": doc_output_path,
        }

    validator = LlamaPairValidator(
        model_alias=config.primary_model,
        generation_settings=generation_settings,
    )
    validator.load()

    results = [validator.validate_pair(row) for row in rows_to_run]
    write_results_jsonl(results, results_output_path)
    write_validation_markdown(
        results=results,
        skipped_rows=skipped_rows,
        output_path=doc_output_path,
        input_csv_path=input_csv_path,
        model_alias=config.primary_model,
        generation_settings=generation_settings,
        target_example_ids=target_example_ids,
    )
    return {
        "rows_run": len(results),
        "results_output_path": results_output_path,
        "doc_output_path": doc_output_path,
    }
