import re
from typing import List, Dict, Any, Tuple

class NumericDateFeasibilityFilter:
    """Extracts pilot candidate examples targeting numeric/date phenomena."""
    
    def __init__(self, max_span_length: int = 50):
        self.max_span_length = max_span_length

    def is_numeric_or_date_candidate(self, text: str, label_type: str) -> bool:
        """
        SCHEMA UNCERTAINTY: The dataset does not strictly define 'number' hallucination natively.
        We apply conservative heuristics: short span + digit presence.
        We do NOT overclaim this is definitively a true number hallucination until verified.
        """
        if re.search(r'\d+', text):
            return True
        return False

    def filter_records(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        candidates = []
        rejections = {
            "no_labels": 0,
            "no_short_numeric_labels": 0,
            "multiple_competing_numeric_labels": 0,
            "missing_span_data": 0
        }
        
        for record in records:
            labels = record.get("labels_candidate", [])
            
            if not labels:
                rejections["no_labels"] += 1
                continue
                
            valid_numeric_labels = []
            
            for label in labels:
                if "start" not in label or "end" not in label or "text" not in label:
                    continue
                    
                text = label["text"]
                label_type = label.get("label_type", "")
                
                if len(text) <= self.max_span_length and self.is_numeric_or_date_candidate(text, label_type):
                    valid_numeric_labels.append(label)
            
            if len(valid_numeric_labels) == 0:
                if len(labels) > 0 and "start" not in labels[0]:
                    rejections["missing_span_data"] += 1
                else:
                    rejections["no_short_numeric_labels"] += 1
                continue
                
            if len(valid_numeric_labels) > 1:
                # We prefer a single dominant hallucination span to avoid confounding variables
                rejections["multiple_competing_numeric_labels"] += 1
                continue
                
            # Valid candidate with exactly ONE dominant numeric label
            record["dominant_label"] = valid_numeric_labels[0]
            candidates.append(record)
            
        return candidates, rejections
