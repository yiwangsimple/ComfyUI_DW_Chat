import os
import sys
import google.generativeai as genai
from PIL import Image
import torch
from contextlib import contextmanager
from tenacity import retry, stop_after_attempt, wait_exponential
import random

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

class Gemini1_5Base:
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
    def call_api(self, model, prompt, image=None, temperature=0.7, max_tokens=1024):
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        content = [prompt, image] if image else prompt
        response = model.generate_content(content, generation_config=generation_config)
        return response.text

class Gemini1_5Text(Gemini1_5Base):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "你好，请问有什么可以帮助你的吗？", "multiline": True}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.1}),
                "max_tokens": ("INT", {"default": 1024, "min": 1, "max": 2048})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "generate_text"
    CATEGORY = "🌙DW/Gemini1.5"

    def generate_text(self, prompt, temperature, max_tokens):
        if not self.client:
            return ("错误：GEMINI_API_KEY 未设置或无效。请检查您的 api_key.ini 文件。",)

        model = self.client.GenerativeModel('gemini-1.5-flash')

        try:
            with temporary_env_var('HTTP_PROXY', None), temporary_env_var('HTTPS_PROXY', None):
                textoutput = self.call_api(model, prompt, temperature=temperature, max_tokens=max_tokens)
            return (textoutput,)
        except Exception as e:
            return (f"错误: {str(e)}",)

class Gemini1_5Vision(Gemini1_5Base):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "分析这张图片并生成一个详细的文本到图像提示。不要加前缀！", "multiline": True}),
                "image": ("IMAGE",),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.1}),
                "max_tokens": ("INT", {"default": 1024, "min": 1, "max": 2048}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff})    
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("description",)
    FUNCTION = "analyze_image"
    CATEGORY = "🌙DW/Gemini1.5"

    def analyze_image(self, prompt, image, temperature, max_tokens, use_fixed_seed, seed):
        if not self.client:
            return ("错误：GEMINI_API_KEY 未设置或无效。请检查您的 api_key.ini 文件。",)

        model = self.client.GenerativeModel('gemini-1.5-flash')

        try:
            pil_image = self.tensor_to_image(image)
            
            if use_fixed_seed:
                random.seed(seed)
                torch.manual_seed(seed)
            
            with temporary_env_var('HTTP_PROXY', None), temporary_env_var('HTTPS_PROXY', None):
                textoutput = self.call_api(model, prompt, image=pil_image, temperature=temperature, max_tokens=max_tokens)
            
            if use_fixed_seed:
                textoutput = f"[使用固定种子: {seed}]\n\n" + textoutput
            
            return (textoutput,)
        except Exception as e:
            return (f"错误: {str(e)}",)

NODE_CLASS_MAPPINGS = {
    "Gemini1_5Text": Gemini1_5Text,
    "Gemini1_5Vision": Gemini1_5Vision,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Gemini1_5Text": "Gemini 1.5 文本",
    "Gemini1_5Vision": "Gemini 1.5 视觉",
}