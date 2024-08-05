import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import gc
import os

class GemmaDialogueNode:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.precision = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "max_new_tokens": ("INT", {"default": 100, "min": 1, "max": 2000}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.05}),
                "device": (["cuda", "cpu"], {"default": "cpu"}),
                "precision": (["float32", "float16"], {"default": "float32"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate"
    CATEGORY = "🌙DW/Chat"

    def generate(self, prompt, max_new_tokens, top_p, device, precision):
        if self.model is None or self.device != device or self.precision != precision:
            self.device = device
            self.precision = precision
            self.load_model()

        prompt = f"<start_of_turn>user\n{prompt}\n<end_of_turn>\n<start_of_turn>model\n"
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)
        attention_mask = torch.ones_like(input_ids)
        
        pad_token_id = self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.tokenizer.eos_token_id - 1
        
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                top_p=top_p,
                do_sample=True,
                pad_token_id=pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
        response = generated_text.split("<start_of_turn>model\n")[-1].split("<end_of_turn>")[0].strip()

        del input_ids, outputs
        torch.cuda.empty_cache() if self.device == "cuda" else None
        gc.collect()

        return (response,)

    def load_model(self):
        model_path = self.get_model_path()
        
        if not os.path.exists(model_path) or not any(os.scandir(model_path)):
            raise RuntimeError(f"Model not found in {model_path}. Please manually download the model from https://huggingface.co/google/gemma-2b-it and place it in the specified directory.")

        try:
            print(f"Loading model from {model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                str(model_path),
                trust_remote_code=True,
                device_map=self.device,
                torch_dtype=torch.float16 if self.precision == "float16" else torch.float32,
            )
            print("Model loaded successfully")
            
            self.model.to(self.device)
            
        except Exception as e:
            print(f"Error loading model: {e}")
            raise RuntimeError(f"Failed to load the model from {model_path}. Please ensure the model files are correctly placed in the directory.")

        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Failed to load the model or tokenizer")

    def get_model_path(self):
        possible_paths = [
            Path("models/LLavacheckpoints/gemma-2-2b-it"),
            Path("LLavacheckpoints/gemma-2-2b-it"),
            Path("gemma-2-2b-it"),
        ]
        
        for path in possible_paths:
            if path.exists() and any(path.iterdir()):
                return str(path)
        
        raise RuntimeError("Could not find the Gemma model. Please ensure it's placed in one of the expected directories.")

    def unload_model(self):
        del self.model
        del self.tokenizer
        self.model = None
        self.tokenizer = None
        torch.cuda.empty_cache() if self.device == "cuda" else None
        gc.collect()

NODE_CLASS_MAPPINGS = {
    "GemmaDialogueNode": GemmaDialogueNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GemmaDialogueNode": "Gemma 2 IT Dialogue"
}