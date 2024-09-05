import os
import sys
import torch
from PIL import Image
from io import BytesIO
import base64
from contextlib import contextmanager
from tenacity import retry, stop_after_attempt, wait_exponential
from http import HTTPStatus
import dashscope

# 添加父目录到 Python 路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ..api_utils import load_api_key

@contextmanager
def temporary_env_var(key: str, new_value):
    old_value = os.environ.get(key)
    os.environ[key] = new_value if new_value is not None else os.environ.pop(key, None)
    try:
        yield
    finally:
        if old_value is not None:
            os.environ[key] = old_value
        elif key in os.environ:
            del os.environ[key]

class QwenVLBase:
    def __init__(self):
        self.api_key = load_api_key('DASHSCOPE_API_KEY')
        if self.api_key:
            dashscope.api_key = self.api_key
        else:
            print("错误：在 api_key.ini 中未找到 DASHSCOPE_API_KEY")

    @staticmethod
    def tensor_to_image(tensor):
        return Image.fromarray(tensor.squeeze().mul(255).clamp(0, 255).byte().cpu().numpy(), mode='RGB')

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_api(self, prompt, image, model, task, temperature=0.7, max_tokens=1024):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        messages = [
            {
                "role": "system",
                "content": f"You are an AI assistant specialized in {task}. Analyze the image and respond accordingly."
            },
            {
                "role": "user",
                "content": [
                    {"image": img_str},
                    {"text": prompt}
                ]
            }
        ]

        response = dashscope.MultiModalConversation.call(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        if response.status_code == HTTPStatus.OK:
            return response.output.text
        else:
            raise Exception(f"API调用失败: {response.code} - {response.message}")

class Qwen2VLCaption(QwenVLBase):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"default": "分析这张图片并提供详细描述。", "multiline": True}),
                "model": (["qwen-vl-max-0809", "qwen-vl-max", "qwen-vl-plus", "qwen-vl"], {"default": "qwen-vl-max-0809"}),
                "task": (["general", "ocr", "visual_reasoning", "chinese_understanding", "prompt_generation"], {"default": "general"}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.1}),
                "max_tokens": ("INT", {"default": 1024, "min": 1, "max": 2048}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "process_image"
    CATEGORY = "🌙DW/QwenVL"

    def process_image(self, image, prompt, model, task, temperature, max_tokens):
        if not self.api_key:
            return ("错误：DASHSCOPE_API_KEY 未设置或无效。请检查您的 api_key.ini 文件。",)

        try:
            pil_image = self.tensor_to_image(image)
            
            task_prompts = {
                "general": "分析这张图片并提供详细描述。",
                "ocr": "识别并提取图片中的所有文字。",
                "visual_reasoning": "分析图片并回答以下问题：",
                "chinese_understanding": "分析图片并用流畅的中文描述内容。",
                "prompt_generation": "分析这张图片并生成一个详细的文本到图像提示。不要加前缀！"
            }
            
            full_prompt = f"{task_prompts[task]} {prompt}"
            
            with temporary_env_var('HTTP_PROXY', None), temporary_env_var('HTTPS_PROXY', None):
                result = self.call_api(full_prompt, pil_image, model, task, temperature=temperature, max_tokens=max_tokens)
            
            return (result,)
        except Exception as e:
            return (f"错误: {str(e)}",)

NODE_CLASS_MAPPINGS = {
    "Qwen2VLCaption": Qwen2VLCaption,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Qwen2VLCaption": "通义千问VL 多功能视觉分析",
}