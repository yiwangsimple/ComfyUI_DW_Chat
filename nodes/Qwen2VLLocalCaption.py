import os
from pathlib import Path
import torch
from PIL import Image
from torchvision.transforms import ToPILImage
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
import folder_paths
from huggingface_hub import snapshot_download
from accelerate import cpu_offload

# 定义模型文件存储目录
files_for_qwen2_vl_2b = Path(os.path.join(folder_paths.models_dir, "prompt_generator", "Qwen2VLCheckpoints", "files_for_qwen2_vl_2b"))
files_for_qwen2_vl_2b.mkdir(parents=True, exist_ok=True)

class Qwen2VLLocalCaption:
    def __init__(self):
        self.model_id = "Qwen/Qwen2-VL-2B-Instruct"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None

    def load_model(self, quantization):
        if self.model is None or self.processor is None:
            self.model_path = snapshot_download(self.model_id, 
                                                local_dir=str(files_for_qwen2_vl_2b),
                                                local_dir_use_symlinks=False)
            
            if quantization == "8-bit":
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            elif quantization == "4-bit":
                quantization_config = BitsAndBytesConfig(load_in_4bit=True)
            else:
                quantization_config = None

            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                attn_implementation="flash_attention_2",
                quantization_config=quantization_config
            )
            self.processor = AutoProcessor.from_pretrained(self.model_path)

            # CPU offloading
            if self.device == "cuda":
                cpu_offload(self.model, execution_device=self.device, offload_buffers=True)

    def clear_memory(self):
        if self.model is not None:
            del self.model
            self.model = None
        if self.processor is not None:
            del self.processor
            self.processor = None
        torch.cuda.empty_cache()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"default": "分析这张图片并提供详细描述。", "multiline": True}),
                "task": (["general", "ocr", "visual_reasoning", "chinese_understanding", "prompt_generation"], {"default": "general"}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.1}),
                "max_tokens": ("INT", {"default": 1024, "min": 1, "max": 2048}),
                "keep_alive": ("BOOLEAN", {"default": False}),
                "quantization": (["none", "8-bit", "4-bit"], {"default": "none"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "process_image"
    CATEGORY = "🌙DW/Qwen2VL"

    @torch.inference_mode()
    def process_image(self, image, prompt, task, temperature, max_tokens, keep_alive, quantization):
        try:
            self.load_model(quantization)
            
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

            generated_ids = self.model.generate(**inputs, max_new_tokens=max_tokens, temperature=temperature, do_sample=True)
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            if not keep_alive:
                self.clear_memory()
            
            return (generated_text,)
        except Exception as e:
            return (f"错误: {str(e)}",)

NODE_CLASS_MAPPINGS = {
    "Qwen2VLLocalCaption": Qwen2VLLocalCaption
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Qwen2VLLocalCaption": "通义千问VL 本地多功能视觉分析"
}
