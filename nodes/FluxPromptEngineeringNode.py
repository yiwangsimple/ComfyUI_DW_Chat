import os
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Dict, Any, Tuple
import folder_paths
import gc

class FluxPromptEngineeringNode:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.enhancer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = "gokaygokay/Flux-Prompt-Enhance"
        self.model_path = self.get_model_path()
        print(f"Flux-Prompt-Enhance model path: {self.model_path}")

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "input_prompt": ("STRING", {"multiline": True}),
                "max_length": ("INT", {"default": 256, "min": 1, "max": 1024}),
                "device": (["cuda", "cpu"], {"default": "cuda"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "enhance_prompt"
    CATEGORY = "🌙DW/提示词工程"

    def enhance_prompt(self, input_prompt: str, max_length: int = 256, device: str = "cuda") -> Tuple[str]:
        if self.enhancer is None or self.device != device:
            self.device = device
            self.load_model()

        enhanced_input = f"enhance prompt: {input_prompt}"
        try:
            answer = self.enhancer(enhanced_input, max_length=max_length)
            final_answer = answer[0]['generated_text']
            return (final_answer,)
        except Exception as e:
            print(f"提示词增强失败: {str(e)}")
            return (f"【增强失败】{input_prompt}",)

    def load_model(self):
        if self.model_path is None or not os.path.exists(self.model_path):
            raise RuntimeError(f"Model path is invalid or does not exist: {self.model_path}")

        try:
            print(f"Loading model from {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_path,
                device_map=self.device,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            )
            self.enhancer = pipeline('text2text-generation',
                                     model=self.model,
                                     tokenizer=self.tokenizer,
                                     repetition_penalty=1.2,
                                     device=self.device)
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise RuntimeError(f"Failed to load the model from {self.model_path}. Error: {str(e)}")

    def get_model_path(self):
        possible_paths = [
            os.path.join(folder_paths.models_dir, "prompt_generator", "Flux-Prompt-Enhance"),
            "models/prompt_generator/Flux-Prompt-Enhance",
            "Flux-Prompt-Enhance",
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and any(os.scandir(path)):
                return path
        
        raise RuntimeError("Could not find the Flux-Prompt-Enhance model. Please ensure it's placed in one of the expected directories.")

    def unload_model(self):
        del self.model
        del self.tokenizer
        del self.enhancer
        self.model = None
        self.tokenizer = None
        self.enhancer = None
        torch.cuda.empty_cache() if self.device == "cuda" else None
        gc.collect()

NODE_CLASS_MAPPINGS = {
    "FluxPromptEngineeringNode": FluxPromptEngineeringNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FluxPromptEngineeringNode": "Flux 提示词扩展"
}