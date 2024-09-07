import os
import torch
import numpy as np
from PIL import Image
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import folder_paths
import gc
from qwen_vl_utils import process_vision_info
import cv2

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

            print(f"Input image type: {type(image)}")
            if isinstance(image, torch.Tensor):
                print(f"Image tensor shape: {image.shape}")
                
                # 处理特殊的图像形状
                if image.shape == (1, 1, 1152):
                    # 假设这是一个被错误解释的 RGB 图像
                    image = image.squeeze().reshape(16, 24, 3)  # 16 * 24 * 3 = 1152
                elif image.shape[0] == 1:
                    image = image.squeeze(0)
                
                # 确保图像是 3 通道的
                if image.shape[2] != 3:
                    if image.shape[2] == 1:
                        image = image.repeat(1, 1, 3)
                    else:
                        raise ValueError(f"Unexpected number of channels: {image.shape[2]}")
                
                # 转换为 numpy 数组
                image = (image.cpu().numpy() * 255).astype(np.uint8)
                
                # 调整图像大小为模型期望的尺寸（假设为224x224）
                image = cv2.resize(image, (224, 224))
                
                # 转换为 PIL Image
                image = Image.fromarray(image)
            
            print(f"Processed image size: {image.size}, mode: {image.mode}")

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
                        {"type": "image", "image": image},
                        {"type": "text", "text": full_prompt}
                    ]
                }
            ]

            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, _ = process_vision_info(messages)
            inputs = self.processor(text=[text], images=image_inputs, return_tensors="pt").to(self.device)

            with torch.no_grad():
                generated_ids = self.model.generate(**inputs, max_new_tokens=max_tokens, temperature=temperature, do_sample=True)
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # 提取助手的回答
            assistant_response = generated_text.split('assistant\n')[-1].strip()
            
            del inputs, generated_ids
            torch.cuda.empty_cache() if self.device == "cuda" else None
            gc.collect()
            
            return (assistant_response,)
        except Exception as e:
            import traceback
            error_msg = f"错误: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return (error_msg,)

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
            raise RuntimeError(f"Failed to load the model from {self.model_path}. Error: {str(e)}")

    def get_model_path(self):
        possible_paths = [
            os.path.join(folder_paths.models_dir, "prompt_generator", "Qwen2-VL-2B-Instruct"),
            "models/prompt_generator/Qwen2-VL-2B-Instruct",
            "Qwen2-VL-2B-Instruct",
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and any(os.scandir(path)):
                return path
        
        raise RuntimeError("Could not find the Qwen2-VL model. Please ensure it's placed in one of the expected directories.")

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