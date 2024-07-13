import os
import io
from pathlib import Path
import torch
from PIL import Image
from torchvision.transforms import ToPILImage
from transformers import AutoProcessor, AutoModelForCausalLM
import folder_paths

class SD3LongCaptioner:
    def __init__(self):
        self.model_id = "gokaygokay/sd3-long-captioner"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id).to(self.device).eval()
        self.processor = AutoProcessor.from_pretrained(self.model_id)

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
        # Convert the image tensor to PIL Image
        pil_image = ToPILImage()(image[0].permute(2, 0, 1))
        
        # Process the image and prompt
        model_inputs = self.processor(text=prompt, images=pil_image, return_tensors="pt").to(self.device)
        
        # Generate caption
        with torch.inference_mode():
            input_len = model_inputs["input_ids"].shape[-1]
            generation = self.model.generate(
                **model_inputs,
                repetition_penalty=1.05,
                max_new_tokens=512,
                do_sample=False
            )
        
        # Decode the generated text
        generation = generation[0][input_len:]
        decoded = self.processor.decode(generation, skip_special_tokens=True)
        
        return (decoded,)

NODE_CLASS_MAPPINGS = {
    "SD3LongCaptioner": SD3LongCaptioner
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SD3LongCaptioner": "SD3 Long Captioner"
}