import os
import json
from groq import Groq

class GroqChatNode:
    def __init__(self):
        self.client = None
        self.load_api_key()

    def load_api_key(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
                api_key = config.get('GROQ_API_KEY')
                if api_key:
                    self.client = Groq(api_key=api_key)
                else:
                    print("Error: GROQ_API_KEY not found in config.json")
        except FileNotFoundError:
            print(f"Error: config.json not found at {config_path}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in config.json at {config_path}")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (["gemma-7b-it", "llama3-70b-8192", "mixtral-8x7b-32768", "llama3-8b-8192", "llama-3.1-8b-versatile", "llama-3.1-70b-versatile"],),
                "prompt": ("STRING", {"multiline": True}),
                "max_tokens": ("INT", {"default": 1000, "min": 1, "max": 32768}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0, "max": 2, "step": 0.1}),
                "top_p": ("FLOAT", {"default": 1.0, "min": 0, "max": 1, "step": 0.1}),
            },
            "optional": {
                "system_message": ("STRING", {"multiline": True}),
                "presence_penalty": ("FLOAT", {"default": 0, "min": -2, "max": 2, "step": 0.1}),
                "frequency_penalty": ("FLOAT", {"default": 0, "min": -2, "max": 2, "step": 0.1}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate_text"
    CATEGORY = "🌙DW/groqchat"

    def generate_text(self, model, prompt, max_tokens, temperature, top_p, system_message="", presence_penalty=0, frequency_penalty=0):
        if not self.client:
            return ("Error: GROQ_API_KEY not set or invalid. Please check your config.json file.",)

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            chat_completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty
            )
            return (chat_completion.choices[0].message.content,)
        except Exception as e:
            return (f"Error: {str(e)}",)

NODE_CLASS_MAPPINGS = {
    "GroqChatNode": GroqChatNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GroqChatNode": "Groq Chat"
}