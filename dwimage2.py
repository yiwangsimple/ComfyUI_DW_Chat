import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
from pathlib import Path
import folder_paths
import os
import shutil
from torchvision.transforms import ToPILImage

# 定义模型存储目录
models_dir = Path(folder_paths.base_path) / "models"
llava_checkpoints_dir = models_dir / "LLavacheckpoints"
files_for_moondream2 = llava_checkpoints_dir / "files_for_moondream2"
files_for_moondream2.mkdir(parents=True, exist_ok=True)

class Moondream2Predictor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Moondream2Predictor, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.tokenizer = None
        return cls._instance

    def load_model(self):
        if self.model is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"使用设备: {self.device}")
            print("加载模型中...")
            self.model = AutoModelForCausalLM.from_pretrained(files_for_moondream2, trust_remote_code=True).to(self.device)
            self.tokenizer = AutoTokenizer.from_pretrained(files_for_moondream2)
            print("模型加载成功")

    def generate_predictions(self, image_path, question):
        self.load_model()  # 确保模型已加载
        try:
            image_input = Image.open(image_path).convert("RGB")
            enc_image = self.model.encode_image(image_input)
            generated_text = self.model.answer_question(enc_image, question, self.tokenizer)
            return generated_text
        finally:
            if os.path.exists(image_path):
                os.remove(image_path)

    def clear_memory(self):
        if self.model:
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            torch.cuda.empty_cache()

class Moondream2model:
    def __init__(self):
        self.predictor = Moondream2Predictor()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "text_input": ("STRING", {"multiline": True, "default": ""}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "moondream2_generate_predictions"
    CATEGORY = "🌙DW/dwimage2"

    def moondream2_generate_predictions(self, image, text_input):
        pil_image = ToPILImage()(image[0].permute(2, 0, 1))
        temp_path = files_for_moondream2 / "temp_image.png"
        pil_image.save(temp_path)
        
        response = self.predictor.generate_predictions(temp_path, text_input)
        response = ' '.join(response.strip().split())
        
        return (response,)

    def __del__(self):
        self.predictor.clear_memory()

NODE_CLASS_MAPPINGS = {
    "dwimage2": Moondream2model
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "dwimage2": "DW Image2 Chat"
}