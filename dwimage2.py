from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
from pathlib import Path
import torch
from torchvision.transforms import ToPILImage
from huggingface_hub import snapshot_download
import folder_paths
import os
import shutil

# Define the directory for saving files related to your new model
models_dir = Path(folder_paths.base_path) / "models"
llava_checkpoints_dir = models_dir / "LLavacheckpoints"
files_for_moondream2 = llava_checkpoints_dir / "files_for_moondream2"
files_for_moondream2.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

class Moondream2Predictor:
    def __init__(self):
        self.model_path = snapshot_download("vikhyatk/moondream2", 
                                            local_dir=files_for_moondream2,
                                            force_download=False,
                                            local_files_only=False,
                                            revision="main",  # Use the latest version
                                            local_dir_use_symlinks="auto",
                                            ignore_patterns=["*.bin", "*.jpg", "*.png", "*.gguf"])
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        print("Loading model...")
        self.model = AutoModelForCausalLM.from_pretrained(self.model_path, trust_remote_code=True).to(self.device)
        print("Model loaded successfully")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

    def generate_predictions(self, image_path, question):
        try:
            # Load and process the image
            image_input = Image.open(image_path).convert("RGB")
            enc_image = self.model.encode_image(image_input)

            # Generate predictions
            generated_text = self.model.answer_question(enc_image, question, self.tokenizer)

            return generated_text
        finally:
            # Clean up temporary files
            if os.path.exists(image_path):
                os.remove(image_path)

    def __del__(self):
        # Clean up the model when the predictor is destroyed
        del self.model
        del self.tokenizer
        torch.cuda.empty_cache()  # Clear CUDA cache if using GPU

class Moondream2model:
    def __init__(self):
        self.predictor = Moondream2Predictor()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "text_input": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)

    FUNCTION = "moondream2_generate_predictions"

    CATEGORY = "🌙DW/dwimage2"

    def moondream2_generate_predictions(self, image, text_input):
        # Convert tensor image to PIL Image
        pil_image = ToPILImage()(image[0].permute(2, 0, 1))
        temp_path = files_for_moondream2 / "temp_image.png"
        pil_image.save(temp_path)      
        
        response = self.predictor.generate_predictions(temp_path, text_input)
        
        # Post-processing and optimization of the response
        response = response.strip()  # Remove leading/trailing whitespace
        response = ' '.join(response.split())  # Remove extra spaces
        
        return (response, )

    def __del__(self):
        # Clean up when the node is destroyed
        del self.predictor
        # Clear the temporary directory
        if files_for_moondream2.exists():
            shutil.rmtree(files_for_moondream2)

NODE_CLASS_MAPPINGS = {
    "dwimage2": Moondream2model
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "dwimage2": "DW Image2 Chat"
}