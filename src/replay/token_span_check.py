import sys
from typing import Dict, Any, Tuple
from transformers import AutoTokenizer

class TokenSpanChecker:
    def __init__(self, model_name: str = "NousResearch/Llama-2-7b-chat-hf"):
        # We use a fast tokenizer to access return_offsets_mapping=True.
        # NousResearch clone is used to bypass huggingface gating for standard Llama-2.
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        except Exception as e:
            raise RuntimeError(f"Failed to load tokenizer: {e}\nPlease ensure 'transformers' and 'tokenizers' are installed.")

    def check_span(self, text: str, char_start: int, char_end: int) -> Dict[str, Any]:
        """
        Maps a character span [char_start, char_end) to a token span.
        Returns a structured dictionary with findings and ambiguity flags.
        """
        # add_special_tokens=False to map exactly to the string characters provided
        encoding = self.tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
        offsets = encoding.offset_mapping
        tokens = encoding.tokens()
        
        token_start_idx = None
        token_end_idx = None
        
        is_clean = False
        is_ambiguous = False
        notes = []
        
        # Find the token range that covers the character span
        for idx, (tok_start, tok_end) in enumerate(offsets):
            # A token is considered part of the span if it overlaps with [char_start, char_end)
            if tok_end > char_start and tok_start < char_end:
                if token_start_idx is None:
                    token_start_idx = idx
                token_end_idx = idx
                
        if token_start_idx is None or token_end_idx is None:
            return {
                "status": "failed",
                "notes": ["Could not find overlapping tokens for the given span."],
                "token_span": None,
                "first_token_index": None,
                "hallucinated_tokens": [],
                "target_substring": text[char_start:char_end],
                "clean": False,
                "ambiguous": False
            }
            
        first_token_index = token_start_idx
        hallucinated_tokens = tokens[token_start_idx:token_end_idx + 1]
        
        # Check alignment purity
        actual_tok_start = offsets[token_start_idx][0]
        actual_tok_end = offsets[token_end_idx][1]
        
        if actual_tok_start < char_start:
            is_ambiguous = True
            notes.append(f"Start boundary cuts through token '{tokens[token_start_idx]}'. Char start: {char_start}, Token start: {actual_tok_start}.")
            
        # Tolerance of +1 character for trailing spaces or punctuation boundaries 
        if actual_tok_end > char_end + 1: 
            is_ambiguous = True
            notes.append(f"End boundary cuts through token '{tokens[token_end_idx]}'. Char end: {char_end}, Token end: {actual_tok_end}.")
            
        if not is_ambiguous:
            is_clean = True
            notes.append("Clean mapping.")
            
        return {
            "status": "success",
            "clean": is_clean,
            "ambiguous": is_ambiguous,
            "notes": notes,
            "token_span": [token_start_idx, token_end_idx],
            "first_token_index": first_token_index,
            "hallucinated_tokens": hallucinated_tokens,
            "target_substring": text[char_start:char_end]
        }
