import os
import sys
import requests
import json
import configparser
import comfy.utils
import folder_paths
import langdetect

# 添加父目录到 Python 路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api_utils import load_api_key

class DeepSeekTranslator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "source_lang": ("STRING", {"default": "auto"}),
                "target_lang": (["zh", "en"], {"default": "en"}),
                "country": ("STRING", {"default": ""}),
                "clean_after_execution": ("BOOLEAN", {"default": True})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "translate_and_improve"
    CATEGORY = "🌙DW/text"

    def __init__(self):
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.temperature = 0.3  # 设置特殊的temperature值用于翻译
        self.api_key = self.load_api_key()

    def load_api_key(self):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_key.ini')
        config.read(config_path)
        return config.get('DEFAULT', 'DEEPSEEK_API_KEY', fallback='')

    def call_api(self, messages):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": self.temperature
        }
        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return f"API call error: {str(e)}"
        except (KeyError, IndexError) as e:
            return f"Error parsing API response: {str(e)}"

    def translate(self, text, source_lang, target_lang):
        messages = [
            {"role": "system", "content": f"You are a professional translator. Translate the following text from {source_lang} to {target_lang}. Only return the translation, without any explanations or additional comments."},
            {"role": "user", "content": text}
        ]
        return self.call_api(messages)

    def get_suggestions(self, translation, country):
        if not country.strip():
            return ""
        messages = [
            {"role": "system", "content": "You are an expert in cultural localization and translation."},
            {"role": "user", "content": f"Review the following translation and provide suggestions for improvement, considering the cultural context of {country}:\n\n{translation}"}
        ]
        return self.call_api(messages)

    def improve_translation(self, translation, suggestions, target_lang):
        if not suggestions.strip():
            return translation
        messages = [
            {"role": "system", "content": f"You are an expert translator. Translate to {target_lang} and improve the text based on the suggestions. Only return the improved translation, without any explanations or additional comments."},
            {"role": "user", "content": f"Original translation:\n{translation}\n\nSuggestions:\n{suggestions}\n\nImprove the translation, considering these suggestions:"}
        ]
        improved = self.call_api(messages)
    
        # 确保结果是正确的语言
        if not self.is_correct_language(improved, target_lang):
            messages = [
                {"role": "system", "content": f"Translate the following text to {target_lang}. Only return the translation, without any explanations or additional comments."},
                {"role": "user", "content": improved}
            ]
            improved = self.call_api(messages)
    
        return improved

    def is_correct_language(self, text, target_lang):
        try:
            detected = langdetect.detect(text)
            return (detected == 'zh-cn' and target_lang == 'zh') or (detected == 'en' and target_lang == 'en')
        except:
            return False

    def cleanup(self):
        # 重置API key
        self.api_key = self.load_api_key()
        # 可以在这里添加其他清理逻辑，如果有的话

    def translate_and_improve(self, text, source_lang, target_lang, country, clean_after_execution):
        try:
            initial_translation = self.translate(text, source_lang, target_lang)
            
            if not country.strip():
                return (initial_translation,)
            
            suggestions = self.get_suggestions(initial_translation, country)
            improved_translation = self.improve_translation(initial_translation, suggestions, target_lang)
            
            # 移除可能的额外注释或解释
            improved_translation = self.remove_extra_content(improved_translation)
            
            return (improved_translation,)
        finally:
            if clean_after_execution:
                self.cleanup()

    def remove_extra_content(self, text):
        # 尝试找到并移除额外的注释或解释
        lines = text.split('\n')
        cleaned_lines = [line for line in lines if not line.startswith('这个') and not line.startswith('This')]
        return '\n'.join(cleaned_lines)

# ComfyUI 节点映射
NODE_CLASS_MAPPINGS = {
    "DeepSeekTranslator": DeepSeekTranslator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DeepSeekTranslator": "DeepSeek Translator"
}