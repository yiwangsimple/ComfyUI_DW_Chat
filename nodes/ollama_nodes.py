import random
import requests
import asyncio

from PIL import Image
import base64
from io import BytesIO


base_url = "http://localhost:11434"

def get_available_models(base_url):
    try:
        response = requests.get(f"{base_url}/api/tags")
        if response.status_code == 200:
            models = response.json()['models']
            return [model['name'] for model in models]
        else:
            print(f"Error fetching models: {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Error connecting to Ollama: {str(e)}")
        return []

class OllamaImageToText:
    base_url = "http://localhost:11434"
    available_models = []

    @classmethod
    def initialize(cls):
        cls.available_models = get_available_models(cls.base_url)
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "query": ("STRING", {
                    "multiline": True,
                    "default": "describe the image"
                }),
                "model": (s.available_models,) if s.available_models else (["No models found"],),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "top_k": ("FLOAT", {"default": 40, "min": 0, "max": 100, "step": 1}),  # 添加 top_k 参数
                "max_tokens": ("INT", {"default": 100, "min": 1, "max": 1024}),  # 添加 max_tokens 参数
                "keep_alive": (["0", "60m"],),
                
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("description",)
    FUNCTION = "ollama_image_to_text"
    CATEGORY = "🌙DW/ImageToText"

    def ollama_image_to_text(self, images, query, seed, model, top_k, max_tokens, keep_alive):
        images_b64 = []

        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_bytes = base64.b64encode(buffered.getvalue())
            images_b64.append(str(img_bytes, 'utf-8'))

        client = Client(host=self.base_url)
        options = {
            "seed": seed,
            "top_k": top_k,  # 添加 top_k 参数
            "max_tokens": max_tokens,  # 添加 max_tokens 参数
        }

        response = client.generate(model=model, prompt=query, keep_alive=keep_alive, options=options, images=images_b64)

        return (response['response'],)


class OllamaTextToText:
    base_url = "http://localhost:11434"
    available_models = []

    @classmethod
    def initialize(cls):
        cls.available_models = get_available_models(cls.base_url)

    @classmethod
    def INPUT_TYPES(s):
        seed = random.randint(1, 2 ** 31)
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "1girl"
                }),
                "model": (s.available_models,) if s.available_models else (["No models found"],),
                "extra_model": ("STRING", {
                    "multiline": False,
                    "default": "none"
                }),
                "system": ("STRING", {
                    "multiline": True,
                    "default": "You are creating a prompt for Stable Diffusion to generate an image. First step: understand the input and generate a text prompt for the input. Second step: only respond in English with the prompt itself in phrase, but embellish it as needed but keep it under 200 tokens.",
                    "title":"system"
                }),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "top_k": ("FLOAT", {"default": 40, "min": 0, "max": 100, "step": 1}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0, "max": 1, "step": 0.05}),
                "temperature": ("FLOAT", {"default": 0.5, "min": 0, "max": 1, "step": 0.05}),
                "max_tokens": ("INT", {"default": 100, "min": 1, "max": 1024}),  # 添加 max_tokens 参数
                "tfs_z": ("FLOAT", {"default": 1, "min": 1, "max": 1000, "step": 0.05}),
                "keep_alive": (["0", "60m"],),
            },"optional": {
                "context": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING","STRING",)
    RETURN_NAMES = ("response","context",)
    FUNCTION = "ollama_text_to_text"
    CATEGORY = "🌙DW/Chat"

    def ollama_text_to_text(self, prompt, model, extra_model, system, seed, top_k, top_p,temperature,max_tokens,tfs_z, keep_alive, context=None):

        client = Client(host=self.base_url)

        options = {
            "seed": seed,
            "top_k":top_k,
            "top_p":top_p,
            "temperature":temperature,
            "max_tokens":max_tokens,  # 添加 max_tokens 参数
            "tfs_z":tfs_z,
        }
            
        if extra_model != "none":
            model = extra_model
        response = client.generate(model=model, system=system, prompt=prompt, keep_alive=keep_alive, context=context, options=options)

        return (response['response'],response['context'],)

# 初始化模型列表
OllamaImageToText.initialize()
OllamaTextToText.initialize()

NODE_CLASS_MAPPINGS = {
    "OllamaImageToText": OllamaImageToText,
    "OllamaTextToText": OllamaTextToText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OllamaImageToText": "Ollama Image To Text",
    "OllamaTextToText": "Ollama Text To Text",
}