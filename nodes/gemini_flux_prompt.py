import os
import sys
import google.generativeai as genai
from PIL import Image
import torch
from contextlib import contextmanager
from tenacity import retry, stop_after_attempt, wait_exponential

# 添加父目录到 Python 路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api_utils import load_api_key

@contextmanager
def temporary_env_var(key: str, new_value):
    old_value = os.environ.get(key)
    if new_value is not None:
        os.environ[key] = new_value
    elif key in os.environ:
        del os.environ[key]
    try:
        yield
    finally:
        if old_value is not None:
            os.environ[key] = old_value
        elif key in os.environ:
            del os.environ[key]

class GeminiFluxPrompt:
    def __init__(self):
        self.client = None
        self.load_api_key()

    def load_api_key(self):
        api_key = load_api_key('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key, transport='rest')
            self.client = genai
        else:
            print("错误：在 api_key.ini 中未找到 GEMINI_API_KEY")

    @staticmethod
    def tensor_to_image(tensor):
        tensor = tensor.cpu()
        image_np = tensor.squeeze().mul(255).clamp(0, 255).byte().numpy()
        return Image.fromarray(image_np, mode='RGB')

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_api(self, model, prompt, image=None):
        content = [prompt, image] if image else prompt
        response = model.generate_content(content)
        return response.text

    def generate_prompt(self, text_input, image_input=None):
        if not self.client:
            return "错误：GEMINI_API_KEY 未设置或无效。请检查您的 api_key.ini 文件。", ""

        model = self.client.GenerativeModel('gemini-1.5-pro')

        system_prompt = """你是一位有艺术气息的Stable Diffusion prompt 助理。你的任务是根据给定的主题生成一份详细的、高质量的prompt，让Stable Diffusion可以生成高质量的图像。prompt必须包含"clip-L:"和"clip-T5:"两部分。请严格按照以下格式输出：

clip-L: [英文关键词，用逗号分隔]

clip-T5: [英文自然语言描述]

注意：
1. clip-L 部分只包含关键词或短语，不要有完整句子或解释。
2. clip-T5 部分使用自然语言描述。
3. 两个部分都必须是英文。
4. 确保描述人物时包含面部细节，如"beautiful detailed eyes, beautiful detailed lips, extremely detailed eyes and face, long eyelashes"。
5. 添加至少5个合理的画面细节。
6. 包含材质、艺术风格、色彩色调和灯光效果的描述。
7. 必须同时生成 clip-L 和 clip-T5 两部分内容。
"""

        if image_input is not None:
            pil_image = self.tensor_to_image(image_input)
            if text_input:
                user_prompt = f"请分析这张图片，并结合以下文本生成Stable Diffusion prompt。文本：{text_input}"
            else:
                user_prompt = "请分析这张图片，并生成相应的Stable Diffusion prompt。"
        else:
            pil_image = None
            user_prompt = f"请根据以下主题生成Stable Diffusion prompt：{text_input}"

        try:
            with temporary_env_var('HTTP_PROXY', None), temporary_env_var('HTTPS_PROXY', None):
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = self.call_api(model, full_prompt, image=pil_image)
            
            # 分离 clip-L 和 clip-T5
            clip_l = ""
            clip_t5 = ""
            current_section = ""
            for line in response.split('\n'):
                if line.startswith("clip-L:"):
                    current_section = "clip-L"
                    clip_l = line.replace("clip-L:", "").strip()
                elif line.startswith("clip-T5:"):
                    current_section = "clip-T5"
                    clip_t5 = line.replace("clip-T5:", "").strip()
                elif current_section == "clip-T5":
                    clip_t5 += " " + line.strip()

            if not clip_l or not clip_t5:
                raise ValueError("API 未能生成有效的 clip-L 和 clip-T5 内容")

            return clip_l, clip_t5
        except Exception as e:
            return f"错误: {str(e)}", f"错误: {str(e)}"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_input": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "image_input": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("clip_L", "clip_T5")
    FUNCTION = "generate"
    CATEGORY = "🌙DW/Gemini1.5"

    def generate(self, text_input, image_input=None):
        return self.generate_prompt(text_input, image_input)

NODE_CLASS_MAPPINGS = {
    "GeminiFluxPrompt": GeminiFluxPrompt
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GeminiFluxPrompt": "Gemini Flux Prompt"
}