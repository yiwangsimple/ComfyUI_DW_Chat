import os
from pathlib import Path
import torch
from PIL import Image
from torchvision.transforms import ToPILImage
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import folder_paths
import gc
import platform

class Qwen2VLLocalCaption:
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = None
        self.precision = None
        print(f"ComfyUI models directory: {folder_paths.models_dir}")
        self.model_path = self.get_model_path()
        print(f"Qwen2-VL model path: {self.model_path}")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"default": "分析这张图片并提供详细描述。", "multiline": True}),
                "task": (["general", "ocr", "visual_reasoning", "chinese_understanding", "prompt_generation"], {"default": "general"}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.1}),
                "max_tokens": ("INT", {"default": 1024, "min": 1, "max": 2048}),
                "device": (["cuda", "cpu"], {"default": "cuda"}),
                "precision": (["float32", "float16"], {"default": "float16"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "process_image"
    CATEGORY = "🌙DW/Qwen2VL"

    def process_image(self, image, prompt, task, temperature, max_tokens, device, precision):
        try:
            if self.model is None or self.device != device or self.precision != precision:
                self.device = device
                self.precision = precision
                self.load_model()

            pil_image = ToPILImage()(image.squeeze().cpu())
            
            task_prompts = {
                "general": "分析这张图片并提供详细描述。",
                "ocr": "识别并提取图片中的所有文字。",
                "visual_reasoning": "分析图片并回答以下问题：",
                "chinese_understanding": "分析图片并用流畅的中文描述内容。",
                "prompt_generation": "分析这张图片并生成一个详细的文本到图像提示。不要加前缀！"
            }
            
            full_prompt = f"{task_prompts[task]} {prompt}"
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": pil_image},
                        {"text": full_prompt}
                    ]
                }
            ]

            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[text], images=[pil_image], return_tensors="pt").to(self.device)

            with torch.no_grad():
                generated_ids = self.model.generate(**inputs, max_new_tokens=max_tokens, temperature=temperature, do_sample=True)
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            del inputs, generated_ids
            torch.cuda.empty_cache() if self.device == "cuda" else None
            gc.collect()
            
            return (generated_text,)
        except Exception as e:
            return (f"错误: {str(e)}",)

    def load_model(self):
        if self.model_path is None or not os.path.exists(self.model_path):
            raise RuntimeError(f"Model path is invalid or does not exist: {self.model_path}")

        try:
            print(f"Loading model from {self.model_path}")
            self.processor = AutoProcessor.from_pretrained(self.model_path, trust_remote_code=True)
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                device_map=self.device,
                torch_dtype=torch.float16 if self.precision == "float16" else torch.float32,
            )
            print("Model loaded successfully")
            
            self.model.to(self.device)
            
        except Exception as e:
            print(f"Error loading model: {e}")
            # 尝试列出模型目录的内容
            try:
                print(f"Contents of model directory:")
                for item in os.listdir(self.model_path):
                    print(f"  - {item}")
            except Exception as dir_error:
                print(f"Error listing model directory: {dir_error}")
            raise RuntimeError(f"Failed to load the model from {self.model_path}. Error: {str(e)}")

    def get_model_path(self):
        possible_paths = [
            Path(folder_paths.models_dir) / "prompt_generator" / "Qwen2-VL-2B-Instruct",
            Path("models/prompt_generator/Qwen2-VL-2B-Instruct"),
            Path("Qwen2-VL-2B-Instruct"),
        ]
        
        for path in possible_paths:
            print(f"Checking path: {path}")
            if path.exists():
                print(f"Path exists: {path}")
                if any(path.iterdir()):
                    print(f"Path contains files: {path}")
                    print(f"Files in directory: {list(path.iterdir())}")
                    return str(path)
                else:
                    print(f"Path is empty: {path}")
            else:
                print(f"Path does not exist: {path}")
        
        print("Could not find the Qwen2-VL model in any of the expected directories.")
        return None

    def unload_model(self):
        del self.model
        del self.processor
        self.model = None
        self.processor = None
        torch.cuda.empty_cache() if self.device == "cuda" else None
        gc.collect()

NODE_CLASS_MAPPINGS = {
    "Qwen2VLLocalCaption": Qwen2VLLocalCaption
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Qwen2VLLocalCaption": "通义千问VL 本地多功能视觉分析"
}