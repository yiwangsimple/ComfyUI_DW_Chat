import os
from pathlib import Path
import torch
from PIL import Image
from torchvision.transforms import ToPILImage
from transformers import AutoProcessor, PaliGemmaForConditionalGeneration, BitsAndBytesConfig
import folder_paths
from huggingface_hub import snapshot_download
import gc
import random

# 定义模型文件存储目录
files_for_paligemma_3b_pt_224 = Path(os.path.join(folder_paths.models_dir, "PaliGemmaCheckpoints", "files_for_paligemma_3b_pt_224"))
files_for_paligemma_3b_pt_224.mkdir(parents=True, exist_ok=True)

class PaliGemma3bCaptioner:
    def __init__(self):
        self.model_id = "google/paligemma-3b-pt-224"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None

    def load_model(self, quantization):
        if self.model is None or self.processor is None:
            self.model_path = snapshot_download(self.model_id, 
                                                local_dir=files_for_paligemma_3b_pt_224,
                                                force_download=False,
                                                local_files_only=False,
                                                local_dir_use_symlinks="auto")
            
            if quantization == "8-bit":
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            elif quantization == "4-bit":
                quantization_config = BitsAndBytesConfig(load_in_4bit=True)
            else:
                quantization_config = None
            
            self.model = PaliGemmaForConditionalGeneration.from_pretrained(
                self.model_path,
                quantization_config=quantization_config,
                device_map=self.device
            ).eval()
            self.processor = AutoProcessor.from_pretrained(self.model_path)

    def clear_memory(self):
        if self.model is not None:
            del self.model
            self.model = None
        if self.processor is not None:
            del self.processor
            self.processor = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"multiline": False, "default": "caption"}),
                "task_prefix": (["caption", "detect", "segment"], {"default": "caption"}),
                "language": (["en", "es", "fr", "de", "zh"], {"default": "en"}),
                "max_tokens": ("INT", {"default": 100, "min": 1, "max": 512}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "top_k": ("INT", {"default": 50, "min": 1, "max": 100}),
                "quantization": (["none", "8-bit", "4-bit"], {"default": "none"}),
                "control_after_generate": (["fixed", "increment", "decrement", "randomize"], {"default": "fixed"}),
            },
            "optional": {
                "keep_alive": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("caption", "seed")
    FUNCTION = "generate_caption"
    CATEGORY = "🌙DW/ImageToText"

    def generate_caption(self, image, prompt, task_prefix, language, max_tokens, seed, top_k, quantization, control_after_generate, keep_alive=False):
        self.load_model(quantization)  # 确保模型已加载
        
        torch.manual_seed(seed)
        
        pil_image = ToPILImage()(image[0].permute(2, 0, 1))
        
        full_prompt = f"{task_prefix} {language}: {prompt}"
        model_inputs = self.processor(text=full_prompt, images=pil_image, return_tensors="pt").to(self.device)
        
        with torch.inference_mode():
            generation = self.model.generate(
                **model_inputs,
                max_new_tokens=max_tokens,
                do_sample=True,
                top_k=top_k,
                num_return_sequences=1
            )
        
        decoded = self.processor.decode(generation[0], skip_special_tokens=True)
        decoded = decoded.replace(full_prompt, "", 1).strip()
        
        # 根据control_after_generate参数调整seed值
        if control_after_generate == "increment":
            seed += 1
        elif control_after_generate == "decrement":
            seed -= 1
        elif control_after_generate == "randomize":
            seed = random.randint(0, 0xffffffffffffffff)
        # "fixed"选项不需要改变seed值
        
        if not keep_alive:
            self.clear_memory()
        
        return (decoded, seed)

NODE_CLASS_MAPPINGS = {
    "PaliGemma3bCaptioner": PaliGemma3bCaptioner
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PaliGemma3bCaptioner": "PaliGemma 3B Captioner"
}