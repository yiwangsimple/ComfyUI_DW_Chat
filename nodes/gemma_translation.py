import torch
from pathlib import Path
import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import gc
from typing import List, Tuple, Optional, Dict, Any, Generator
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import psutil
import langdetect

class GemmaMultiRoleNode:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.precision = None
        self.last_used_time = 0
        self.translation_cache = {}
        self.interrupt_flag = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "role": (["通用", "报错助手", "标题党", "灵感助手", "小红书", "信息提取", "翻译助手"],),
                "text_input": ("STRING", {"multiline": True}),
                "max_new_tokens": ("INT", {"default": 1000, "min": 1, "max": 4000}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.05}),
                "device": (["cuda", "cpu"], {"default": "cuda"}),
                "precision": (["float32", "float16"], {"default": "float16"}),
                "quality": (["fast", "balanced", "high"], {"default": "balanced"}),
            },
            "optional": {
                "target_lang": (["zh", "en"], {"default": "en"}),
                "country": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "process_text"
    CATEGORY = "🌙DW/MultiRole"

    def process_text(self, role: str, text_input: str, max_new_tokens: int, top_p: float, device: str, 
                     precision: str, quality: str, target_lang: str = "en", country: str = "") -> Tuple[str]:
        if not text_input.strip():
            raise ValueError("Input text is empty or contains only whitespace.")

        async def async_process():
            await self.load_or_update_model(device, precision)
            await self.warm_up_model()

            if role == "翻译助手":
                return await self.translate_and_improve(text_input, "auto", target_lang, country)
            else:
                prompt = self.construct_prompt(role, text_input)
                temperature, top_p = self.get_adaptive_params(text_input, quality)
                result = await self.generate_text(prompt, max_new_tokens, temperature, top_p)
                return self.post_process_result(role, result)

        result = asyncio.run(async_process())
        return (result,)

    async def translate_and_improve(self, text: str, source_lang: str, target_lang: str, country: str) -> str:
        initial_translation = await self.translate(text, source_lang, target_lang)
        
        if not country.strip():
            return initial_translation
        
        suggestions = await self.get_suggestions(initial_translation, country)
        improved_translation = await self.improve_translation(initial_translation, suggestions, target_lang)
        
        return self.remove_extra_content(improved_translation)

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        prompt = f"Translate the following text from {source_lang} to {target_lang}:\n\n{text}\n\nTranslation:"
        return await self.generate_text(prompt, 1000, 0.3, 0.95)

    async def get_suggestions(self, translation: str, country: str) -> str:
        prompt = f"Review the following translation and provide suggestions for improvement, considering the cultural context of {country}:\n\n{translation}\n\nSuggestions:"
        return await self.generate_text(prompt, 500, 0.7, 0.95)

    async def improve_translation(self, translation: str, suggestions: str, target_lang: str) -> str:
        prompt = f"Improve the following translation based on the suggestions, ensuring the result is in {target_lang}:\n\nOriginal translation:\n{translation}\n\nSuggestions:\n{suggestions}\n\nImproved translation:"
        improved = await self.generate_text(prompt, 1000, 0.3, 0.95)
        
        if not self.is_correct_language(improved, target_lang):
            prompt = f"Translate the following text to {target_lang}:\n\n{improved}\n\nTranslation:"
            improved = await self.generate_text(prompt, 1000, 0.3, 0.95)
        
        return improved

    def is_correct_language(self, text: str, target_lang: str) -> bool:
        try:
            detected = langdetect.detect(text)
            return (detected == 'zh-cn' and target_lang == 'zh') or (detected == 'en' and target_lang == 'en')
        except:
            return False

    def remove_extra_content(self, text: str) -> str:
        lines = text.split('\n')
        cleaned_lines = [line for line in lines if not line.startswith('这个') and not line.startswith('This')]
        return '\n'.join(cleaned_lines)

    async def generate_text(self, prompt: str, max_new_tokens: int, temperature: float, top_p: float) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=2048)
        input_ids = inputs.input_ids.to(self.device)
        attention_mask = inputs.attention_mask.to(self.device)
        
        pad_token_id = self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.tokenizer.eos_token_id - 1
        
        with torch.no_grad():
            outputs = await asyncio.to_thread(
                self.model.generate,
                input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        result = generated_text.split(prompt)[-1].strip()

        del input_ids, attention_mask, outputs
        torch.cuda.empty_cache() if self.device == "cuda" else None
        gc.collect()

        return result

    async def load_or_update_model(self, device: str, precision: str):
        current_time = time.time()
        if (self.model is None or self.device != device or self.precision != precision or 
            current_time - self.last_used_time > 3600):
            self.device = device
            self.precision = precision
            await self.load_model()
        self.last_used_time = current_time

    async def load_model(self):
        model_path = self.get_model_path()
        
        if not os.path.exists(model_path) or not any(os.scandir(model_path)):
            raise RuntimeError(f"Model not found in {model_path}. Please manually download the model from https://huggingface.co/google/gemma-2b-it and place it in the specified directory.")

        try:
            print(f"Loading model from {model_path}")
            self.tokenizer = await asyncio.to_thread(AutoTokenizer.from_pretrained, model_path, trust_remote_code=True)
            
            self.model = await asyncio.to_thread(
                AutoModelForCausalLM.from_pretrained,
                model_path,
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

    async def warm_up_model(self):
        warm_up_text = "This is a warm-up text to prepare the model for various tasks."
        warm_up_prompt = self.construct_prompt("通用", warm_up_text)
        await self.generate_text(warm_up_prompt, 50, 0.7, 0.95)

    def get_adaptive_params(self, text: str, quality: str) -> Tuple[float, float]:
        chunk_complexity = self.estimate_complexity(text)
        base_temperature = {"fast": 0.9, "balanced": 0.7, "high": 0.5}[quality]
        base_top_p = {"fast": 0.95, "balanced": 0.92, "high": 0.9}[quality]

        temperature = max(0.1, min(1.0, base_temperature + chunk_complexity * 0.1))
        top_p = max(0.1, min(1.0, base_top_p - chunk_complexity * 0.05))

        return temperature, top_p

    def estimate_complexity(self, text: str) -> float:
        word_count = len(text.split())
        unique_words = len(set(text.lower().split()))
        return min(1.0, max(0.0, (unique_words / word_count - 0.5) * 2))

    def construct_prompt(self, role: str, text: str) -> str:
        prompts = {
            "通用": f"请回答以下问题或完成以下任务：\n\n{text}\n\n回答：",
            "报错助手": f"我是一个Python开发专家，专注于解决代码错误和优化。请分析以下代码或错误信息，并提供详细的解决方案：\n\n{text}\n\n分析和解决方案：",
            "标题党": f"我是一个自媒体创作专家，擅长创作吸引眼球的标题。请为以下内容创作5个吸引人的标题：\n\n{text}\n\n标题：",
            "灵感助手": f"我是一个AI艺术提示词优化专家。请优化以下提示词，重点关注人体完整性、服装设计、光影效果和整体成像质量：\n\n{text}\n\n优化后的提示词：",
            "小红书": f"我是小红书爆款写作专家。请根据以下主题创作一篇小红书文章，包括5个标题和1个正文：\n\n{text}\n\n小红书文章：",
            "信息提取": f"我是一个数据分析工程师。请总结以下内容的要点，并以markdown格式返回：\n\n{text}\n\n总结：",
        }
        return prompts.get(role, f"请回答：\n\n{text}\n\n回答：")

    def post_process_result(self, role: str, result: str) -> str:
        if role == "标题党":
            titles = result.split('\n')
            return '\n'.join([f"{i+1}. {title}" for i, title in enumerate(titles[:5])])
        elif role == "小红书":
            parts = result.split('\n\n', 1)
            titles = parts[0].split('\n')
            content = parts[1] if len(parts) > 1 else ""
            formatted_titles = '\n'.join([f"{i+1}. {title}" for i, title in enumerate(titles[:5])])
            return f"标题：\n{formatted_titles}\n\n正文：\n{content}"
        else:
            return result

    def interrupt(self):
        self.interrupt_flag = True

    def resume(self):
        self.interrupt_flag = False

NODE_CLASS_MAPPINGS = {
    "GemmaMultiRoleNode": GemmaMultiRoleNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GemmaMultiRoleNode": "Gemma Multi-Role Assistant"
}