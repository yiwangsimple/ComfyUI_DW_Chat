import os
import json
import requests

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

class OllamaPromptExtractor:
    base_url = "http://localhost:11434"
    available_models = []

    @classmethod
    def initialize(cls):
        cls.load_config()
        cls.available_models = get_available_models(cls.base_url)

    @classmethod
    def load_config(cls):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
                cls.base_url = config.get('OLLAMA_API_URL', cls.base_url)
            print(f"Loaded Ollama API URL: {cls.base_url}")
        except FileNotFoundError:
            print(f"Warning: config.json not found at {config_path}. Using default URL: {cls.base_url}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in config.json at {config_path}. Using default URL: {cls.base_url}")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (cls.available_models,) if cls.available_models else (["No models found"],),
                "extra_model": ("STRING", {
                    "multiline": False,
                    "default": "none"
                }),
                "theme": ("STRING", {"multiline": True}),
                "max_tokens": ("INT", {"default": 1000, "min": 1, "max": 32768}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0, "max": 2, "step": 0.1}),
                "prompt_type": (["sdxl", "kolors"],),
                "debug": (["enable", "disable"],),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt")
    FUNCTION = "generate_sd_prompt"
    CATEGORY = "🌙DW/prompt_utils"

    def generate_sd_prompt(self, model, extra_model, theme, max_tokens, temperature, prompt_type, debug):
        if extra_model != "none":
            model = extra_model

        if prompt_type == "sdxl":
            system_message = """你是一位有艺术气息的Stable Diffusion prompt 助理。你的任务是根据给定的主题生成高质量的Stable Diffusion提示词。请严格遵循以下要求：

1. 输出格式：
   - 以"Prompt:"开头的正面提示词
   - 以"Negative Prompt:"开头的负面提示词

2. Prompt要求：
   - 开头必须包含"(best quality,4k,8k,highres,masterpiece:1.2),ultra-detailed,(realistic,photorealistic,photo-realistic:1.37)"
   - 包含画面主体、材质、附加细节、图像质量、艺术风格、色彩色调、灯光等
   - 对于人物主题，必须描述眼睛、鼻子、嘴唇
   - 使用英文半角逗号分隔
   - 不超过40个标签，60个单词
   - 按重要性排序

3. Negative Prompt要求：
   - 必须包含"nsfw,(low quality,normal quality,worst quality,jpeg artifacts),cropped,monochrome,lowres,low saturation,((watermark)),(white letters)"
   - 如果是人物主题，还要包含"skin spots,acnes,skin blemishes,age spot,mutated hands,mutated fingers,deformed,bad anatomy,disfigured,poorly drawn face,extra limb,ugly,poorly drawn hands,missing limb,floating limbs,disconnected limbs,out of focus,long neck,long body,extra fingers,fewer fingers,,(multi nipples),bad hands,signature,username,bad feet,blurry,bad body"

请直接生成prompt，不要包含任何解释或额外文字。只使用英文，即使主题是中文。"""
        else:  # prompt_type == "kolors"
            system_message = """你是一位熟练的AI艺术生成模型kolors的提示工程师，类似于DALLE-3。你对提示词的复杂性有深入的理解，确保生成的艺术作品符合用户的期望。你的任务是根据给定的主题生成高质量的kolors提示词。请严格遵循以下要求：

1. 输出格式：
   - 直接输出中文提示词，不需要任何标题或前缀

2. 提示词要求：
   - 使用中文自然语言描述，明确＋精简
   - 先把最难生成的部分写在前面（而非主角），然后写必要的元素和细节，接着是背景，然后是风格、颜色等
   - 加入画面场景细节或人物细节，让图像看起来更充实和合理
   - 确保内容与主题相符，画面整体和谐

请直接生成prompt，不要包含任何解释或额外文字。不要包含负向提示词。"""

        prompt = f"根据以下主题生成{'Stable Diffusion' if prompt_type == 'sdxl' else 'kolors'}提示词：{theme}"

        if debug == "enable":
            print(f"Attempting to connect to Ollama at: {self.base_url}")
            print(f"Using model: {model}")
            print(f"Prompt: {prompt}")

        try:
            response = requests.post(f"{self.base_url}/api/generate", json={
                "model": model,
                "prompt": f"{system_message}\n\nHuman: {prompt}\n\nAssistant:",
                "stream": False,
                "max_tokens": max_tokens,
                "temperature": temperature
            })
            response.raise_for_status()
            result = response.json()
            generated_text = result['response']

            if debug == "enable":
                print(f"Generated text: {generated_text}")

            # 分割正面和负面提示词
            if prompt_type == "sdxl":
                if "Prompt:" in generated_text and "Negative Prompt:" in generated_text:
                    parts = generated_text.split("Negative Prompt:")
                    positive_prompt = parts[0].replace("Prompt:", "").strip()
                    negative_prompt = parts[1].strip()
                else:
                    positive_prompt = generated_text
                    negative_prompt = ""
            else:  # prompt_type == "kolors"
                positive_prompt = generated_text.strip()
                negative_prompt = "低质量，坏手，水印"
            
            return (positive_prompt, negative_prompt)
        except requests.RequestException as e:
            error_message = f"Error: {str(e)}"
            if debug == "enable":
                print(error_message)
            return (error_message, "")

OllamaPromptExtractor.initialize()

NODE_CLASS_MAPPINGS = {
    "OllamaPromptExtractor": OllamaPromptExtractor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OllamaPromptExtractor": "Ollama Prompt Extractor"
}