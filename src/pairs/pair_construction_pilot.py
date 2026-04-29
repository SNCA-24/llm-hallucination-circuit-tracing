import json
from typing import List, Dict, Any

class PairConstructionScaffold:
    def __init__(self, allowed_edit_classes: List[str]):
        self.allowed_edit_classes = allowed_edit_classes

    def extract_context_excerpt(self, source_info: str) -> str:
        """
        Extracts a readable context excerpt limit from the potentially long source context.
        """
        if not source_info:
            return ""
        # Provide the first ~1000 characters as an excerpt to help human reviewers
        if len(source_info) > 1000:
            return source_info[:1000] + "... [TRUNCATED]"
        return source_info

    def build_candidate_record(self, curated_example: Dict[str, Any], token_feasibility: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge raw curated context and token feasibility results into a pair-construction object
        with empty placeholder fields optimized for manual truth recovery.
        """
        dominant_label = curated_example.get("dominant_label", {})
        
        response = curated_example.get("response_candidate", "")
        
        raw = curated_example.get("raw", {})
        
        source_id = raw.get("source_id", "")
        source_category = raw.get("source", "")
        task_type = raw.get("task_type", "")
        
        # In RAGTruth, ground_truth might be an object, string, or metadata. We isolate it raw natively.
        raw_ground_truth_field = raw.get("ground_truth", "")
        
        raw_prompt_field = raw.get("prompt", "")
        raw_source_info_field = raw.get("source_info", "")
        
        clean_input_text_for_validation = ""
        prompt_warning = ""
        if raw_prompt_field:
            clean_input_text_for_validation = raw_prompt_field
        elif raw_source_info_field:
            clean_input_text_for_validation = raw_source_info_field
            prompt_warning = "WARNING: 'prompt' missing in raw data. Using 'source_info' as fallback for input constraint."
            
        record = {
            "example_id": curated_example.get("example_id"),
            
            # Context
            "source_id": source_id,
            "source_category": source_category,
            "task_type": task_type,
            
            # The Generation Fields
            "raw_prompt_field": raw_prompt_field,
            "raw_source_info_field": raw_source_info_field,
            "original_response": response,
            
            # Explicit Clean Validation Input
            "clean_input_text_for_validation": clean_input_text_for_validation,
            "prompt_fallback_warning": prompt_warning,
            
            # The Hallucination targets
            "hallucinated_substring": dominant_label.get("text", ""),
            "hallucinated_char_span": f"[{dominant_label.get('start')}, {dominant_label.get('end')}]",
            "hallucinated_token_span": str(token_feasibility.get("token_span", [])),
            "first_hallucinated_token_index": token_feasibility.get("first_token_index"),
            
            # Truth Recovery Support
            "raw_ground_truth_field": raw_ground_truth_field if isinstance(raw_ground_truth_field, str) else json.dumps(raw_ground_truth_field),
            "supporting_context_excerpt": self.extract_context_excerpt(raw_source_info_field),
            
            # -------------------------------------------------------------
            # BLANK PLACEHOLDERS FOR MANUAL HUMAN TRUTH RECOVERY & PAIR AUTHORING 
            # -------------------------------------------------------------
            "ground_truth_text_verified": None,
            "corrupted_prompt_candidate": None,
            "edit_class": None,
            "edit_delta_text": None,
            "why_minimal": None,
            
            # -------------------------------------------------------------
            # DOWNSTREAM METADATA
            # -------------------------------------------------------------
            "semantic_equivalence_check": None,
            "clean_reproduction_status": None,
            "corrupted_flip_status": None,
            "reviewer_notes": None
        }
        return record
