import os
import sys
from groq import Groq

# 添加父目录到 Python 路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api_utils import load_api_key

class SDPromptAgent:
    def __init__(self):
        self.client = None
        self.load_api_key()

    def load_api_key(self):
        api_key = load_api_key('GROQ_API_KEY')
        if api_key:
            self.client = Groq(api_key=api_key)
        else:
            print("Error: GROQ_API_KEY not found in api_key.ini")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (["gemma-7b-it", "gemma2-9b-it", "mixtral-8x7b-32768", "llama3-8b-8192", "llama3-70b-8192", "llama3-groq-8b-8192-tool-use-preview", "llama3-groq-70b-8192-tool-use-preview", "llama-3.1-8b-instant", "llama-3.1-70b-versatile"],),
                "theme": ("STRING", {"multiline": True}),
                "max_tokens": ("INT", {"default": 1000, "min": 1, "max": 32768}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0, "max": 2, "step": 0.1}),
                "prompt_type": (["sdxl", "kolors"],),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt")
    FUNCTION = "generate_sd_prompt"
    CATEGORY = "🌙DW/prompt_utils"

    def generate_sd_prompt(self, model, theme, max_tokens, temperature, prompt_type):
        if not self.client:
            return ("Error: GROQ_API_KEY not set or invalid. Please check your api_key.ini file.", "")

        if prompt_type == "sdxl":
            system_message = """你是一位有艺术气息的Stable Diffusion prompt 助理。你的任务是根据给定的主题生成高质量的Stable Diffusion提示词。请严格遵循以下要求：

1. 输出格式：
   - 以"Prompt:"开头的正面提示词
   - 以"Negative Prompt:"开头的负面提示词

2. Prompt要求：
   - 开头必须包含"(best quality,4k,8k,highres,masterpiece:1.2),ultra-detailed,(realistic,photorealistic,photo-realistic:1.37)"
   - 包含画面主体、材质、附加细节、图像质量、艺术风格、色彩色调、灯光等
   - 对于人物主题，必须描述眼睛、鼻子、嘴唵
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

        try:
            chat_completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            response = chat_completion.choices[0].message.content

            # 分割正面和负面提示词
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
            
            return (positive_prompt, negative_prompt)
        except Exception as e:
            return (f"Error: {str(e)}", "")

NODE_CLASS_MAPPINGS = {
    "SDPromptAgent": SDPromptAgent
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SDPromptAgent": "SD Prompt Agent"
}