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
        positive_prompt = ""
        negative_prompt = ""

        # 查找正向提示
        pos_start = input_text.lower().find("**positive prompt:**")
        if pos_start != -1:
            pos_start += len("**positive prompt:**")
            pos_end = input_text.lower().find("**negative prompt:**", pos_start)
            if pos_end == -1:
                pos_end = len(input_text)
            positive_prompt = input_text[pos_start:pos_end].strip()

        # 查找负向提示
        neg_start = input_text.lower().find("**negative prompt:**")
        if neg_start != -1:
            neg_start += len("**negative prompt:**")
            # 查找下一个不是 "negative prompt:" 开头的行
            lines = input_text[neg_start:].split('\n')
            negative_lines = []
            for line in lines:
                if not line.lower().strip().startswith("negative prompt:"):
                    negative_lines.append(line.strip())
                else:
                    # 如果遇到新的 "negative prompt:"，将其后面的内容也包含进来
                    negative_lines.append(line.lower().replace("negative prompt:", "").strip())
            negative_prompt = ' '.join(negative_lines).strip()

        return (positive_prompt, negative_prompt)

NODE_CLASS_MAPPINGS = {
    "PromptExtractorNode": PromptExtractorNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptExtractorNode": "Prompt Extractor"
}