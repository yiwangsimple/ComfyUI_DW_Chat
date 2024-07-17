import os
from pathlib import Path
import torch
from PIL import Image
from torchvision.transforms import ToPILImage
from transformers import AutoProcessor, PaliGemmaForConditionalGeneration
import folder_paths
from huggingface_hub import snapshot_download

# 定义模型文件存储目录
files_for_paligemma_pixelprose = Path(os.path.join(folder_paths.models_dir, "LLavacheckpoints", "files_for_paligemma_pixelprose"))
files_for_paligemma_pixelprose.mkdir(parents=True, exist_ok=True)

class PaliGemmaPixelProse:
    def __init__(self):
        self.model_id = "gokaygokay/PaliGemma-PixelProse"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None

    def load_model(self):
        if self.model is None or self.processor is None:
            self.model_path = snapshot_download(self.model_id, 
                                                local_dir=files_for_paligemma_pixelprose,
                                                force_download=False,
                                                local_files_only=False,
                                                local_dir_use_symlinks="auto")
            self.model = PaliGemmaForConditionalGeneration.from_pretrained(self.model_path).to(self.device).eval()
            self.processor = AutoProcessor.from_pretrained(self.model_path)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"multiline": False, "default": "Describe in detail what's in this image."}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("caption",)
    FUNCTION = "generate_caption"
    CATEGORY = "image/text"

    def generate_caption(self, image, prompt):
        self.load_model()  # 确保模型已加载
        
        # 将图像张量转换为PIL图像
        pil_image = ToPILImage()(image[0].permute(2, 0, 1))
        
        # 处理图像和提示
        model_inputs = self.processor(text=prompt, images=pil_image, return_tensors="pt").to(self.device)
        
        # 生成描述
        with torch.inference_mode():
            input_len = model_inputs["input_ids"].shape[-1]
            generation = self.model.generate(
                **model_inputs,
                repetition_penalty=1.05,
                max_new_tokens=512,
                do_sample=False
            )
        
        # 解码生成的文本
        generation = generation[0][input_len:]
        decoded = self.processor.decode(generation, skip_special_tokens=True)
        
        return (decoded,)

NODE_CLASS_MAPPINGS = {
    "PaliGemmaPixelProse": PaliGemmaPixelProse
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PaliGemmaPixelProse": "PaliGemma PixelProse Caption"
}