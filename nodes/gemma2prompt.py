import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import gc
import os
import random

class Gemma2PromptNode:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.precision = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "theme": ("STRING", {"multiline": True}),
                "max_tokens": ("INT", {"default": 1000, "min": 1, "max": 2000}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.05}),
                "device": (["cuda", "cpu"], {"default": "cpu"}),
                "precision": (["float32", "float16"], {"default": "float32"}),
                "prompt_type": (["sdxl", "kolors"],),
                "seed": ("INT", {"default": -1, "min": -1, "max": 0xffffffffffffffff}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt")
    FUNCTION = "generate_prompt"
    CATEGORY = "🌙DW/prompt_utils"

    def generate_prompt(self, theme, max_tokens, top_p, device, precision, prompt_type, seed):
        if self.model is None or self.device != device or self.precision != precision:
            self.device = device
            self.precision = precision
            self.load_model()

        if seed == -1:
            seed = random.randint(0, 0xffffffffffffffff)
        torch.manual_seed(seed)

        if prompt_type == "sdxl":
            system_message = """You are an artistic Stable Diffusion prompt assistant. Your task is to generate high-quality Stable Diffusion prompts based on the given theme. Please strictly follow these requirements:

1. Output format:
   - Positive prompt starting with "Prompt:"
   - Negative prompt starting with "Negative Prompt:"

2. Prompt requirements:
   - Must start with "(best quality,4k,8k,highres,masterpiece:1.2),ultra-detailed,(realistic,photorealistic,photo-realistic:1.37)"
   - Include main subject, materials, additional details, image quality, artistic style, color scheme, lighting, etc.
   - For character themes, must describe eyes, nose, mouth
   - Use English half-width commas to separate
   - No more than 40 tags, 60 words
   - Sort by importance

3. Negative Prompt requirements:
   - Must include "nsfw,(low quality,normal quality,worst quality,jpeg artifacts),cropped,monochrome,lowres,low saturation,((watermark)),(white letters)"
   - For character themes, also include "skin spots,acnes,skin blemishes,age spot,mutated hands,mutated fingers,deformed,bad anatomy,disfigured,poorly drawn face,extra limb,ugly,poorly drawn hands,missing limb,floating limbs,disconnected limbs,out of focus,long neck,long body,extra fingers,fewer fingers,,(multi nipples),bad hands,signature,username,bad feet,blurry,bad body"

Generate the prompt directly without any explanations or additional text. Use English only, even if the theme is in Chinese."""
        else:  # prompt_type == "kolors"
            system_message = """You are a skilled prompt engineer for the AI art generation model kolors, similar to DALLE-3. You have a deep understanding of prompt complexity to ensure the generated artwork meets user expectations. Your task is to generate high-quality kolors prompts based on the given theme. Please strictly follow these requirements:

1. Output format:
   - Output Chinese prompts directly, without any title or prefix

2. Prompt requirements:
   - Use natural Chinese language, clear + concise
   - Write the most difficult parts to generate first (rather than the main character), then necessary elements and details, followed by background, then style, colors, etc.
   - Add scene or character details to make the image look more complete and reasonable
   - Ensure content matches the theme, overall harmony in the image

Generate the prompt directly without any explanations or additional text. Do not include negative prompts."""

        prompt = f"Generate a {'Stable Diffusion' if prompt_type == 'sdxl' else 'kolors'} prompt based on the following theme: {theme}"

        full_prompt = f"<start_of_turn>user\n{system_message}\n\n{prompt}\n<end_of_turn>\n<start_of_turn>model\n"
        
        input_ids = self.tokenizer(full_prompt, return_tensors="pt").input_ids.to(self.device)
        attention_mask = torch.ones_like(input_ids)
        
        pad_token_id = self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.tokenizer.eos_token_id - 1
        
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_tokens,
                temperature=0.7,
                top_p=top_p,
                do_sample=True,
                pad_token_id=pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
        response = generated_text.split("<start_of_turn>model\n")[-1].split("<end_of_turn>")[0].strip()

        if prompt_type == "sdxl":
            if "Prompt:" in response and "Negative Prompt:" in response:
                parts = response.split("Negative Prompt:")
                positive_prompt = parts[0].replace("Prompt:", "").strip()
                negative_prompt = parts[1].strip()
            else:
                positive_prompt = response
                negative_prompt = ""
        else:  # prompt_type == "kolors"
            positive_prompt = response.strip()
            negative_prompt = "低质量，坏手，水印"

        del input_ids, outputs
        torch.cuda.empty_cache() if self.device == "cuda" else None
        gc.collect()

        return (positive_prompt, negative_prompt)

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
    "Gemma2PromptNode": Gemma2PromptNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Gemma2PromptNode": "Gemma 2 IT Prompt Generator"
}