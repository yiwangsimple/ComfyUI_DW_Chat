import re

class PromptExtractorNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_text": ("STRING", {"multiline": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt")
    FUNCTION = "extract_prompts"
    CATEGORY = "🌙DW/prompt_utils"

    def extract_prompts(self, input_text):
        positive_pattern = r'\*\*Positive Prompt:\*\*\s*"(.+?)"'
        negative_pattern = r'\*\*Negative Prompt:\*\*\s*"(.+?)"'
        
        positive_match = re.search(positive_pattern, input_text, re.DOTALL)
        negative_match = re.search(negative_pattern, input_text, re.DOTALL)
        
        positive_prompt = positive_match.group(1).strip() if positive_match else ""
        negative_prompt = negative_match.group(1).strip() if negative_match else ""
        
        return (positive_prompt, negative_prompt)

NODE_CLASS_MAPPINGS = {
    "PromptExtractorNode": PromptExtractorNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptExtractorNode": "Prompt Extractor"
}