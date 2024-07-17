import os
from pathlib import Path
import torch
from PIL import Image
from torchvision.transforms import ToPILImage
from transformers import AutoProcessor, AutoModelForVision2Seq
import folder_paths
from huggingface_hub import snapshot_download

# 定义模型文件存储目录
files_for_sd3_long_captioner_v2 = Path(os.path.join(folder_paths.models_dir, "LLavacheckpoints", "files_for_sd3_long_captioner_v2"))
files_for_sd3_long_captioner_v2.mkdir(parents=true, exist_ok=True)

class SD3LongCaptionerV2:
    def __init__(self):
        self.model_id = "gokaygokay/sd3-long-captioner-v2"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None

    def load_model(self):
        if self.model is None or self.processor is None:
            self.model_path = snapshot_download(self.model_id, 
                                                local_dir=files_for_sd3_long_captioner_v2,
                                                force_download=False,
                                                local_files_only=False,
                                                local_dir_use_symlinks="auto")
            self.model = AutoModelForVision2Seq.from_pretrained(self.model_path).to(self.device).eval()
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
            generation = self.model.generate(
                **model_inputs,
                repetition_penalty=1.05,
                max_new_tokens=512,
                do_sample=False
            )
        
        # 解码生成的文本
        decoded = self.processor.decode(generation[0], skip_special_tokens=True)
        
        return (decoded,)

NODE_CLASS_MAPPINGS = {
    "SD3LongCaptionerV2": SD3LongCaptionerV2
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SD3LongCaptionerV2": "SD3 Long Captioner V2"
}