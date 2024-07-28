import os
import json
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
import httpx
from openai import OpenAI

# 添加父目录到 Python 路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api_utils import load_api_key

class FileBasedChatNode:
    def __init__(self):
        self.api_key = load_api_key('MOONSHOT_API_KEY')
        if not self.api_key:
            raise ValueError("MOONSHOT_API_KEY not found in api_key.ini")
        self.client = OpenAI(
            base_url="https://api.moonshot.cn/v1",
            api_key=self.api_key,
        )
        self.file_messages = []
        self.conversation_history = []
        self.cache_tag = None

    def load_config(self):
        config_path = Path(__file__).parent / "config.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Config file not found: {config_path}")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "file_paths": ("STRING", {"multiline": True}),
                "user_input": ("STRING", {"multiline": True}),
                "use_cache": ("BOOLEAN", {"default": True}),
                "cache_tag": ("STRING", {"default": "file_cache"}),
                "ttl": ("INT", {"default": 300, "min": 60, "max": 3600})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "chat"
    CATEGORY = "🌙DW/fileBaseChat"

    def upload_files(self, files: List[str]) -> List[Dict[str, Any]]:
        messages = []
        for file in files:
            try:
                with open(file, 'rb') as f:
                    response = httpx.post(
                        f"{self.client.base_url}/files",
                        headers={"Authorization": f"Bearer {self.client.api_key}"},
                        files={"file": f},
                        data={"purpose": "assistants"}
                    )
                response.raise_for_status()
                file_id = response.json()['id']
                
                # 获取文件内容
                content_response = httpx.get(
                    f"{self.client.base_url}/files/{file_id}/content",
                    headers={"Authorization": f"Bearer {self.client.api_key}"}
                )
                content_response.raise_for_status()
                file_content = content_response.text
                
                messages.append({
                    "role": "system",
                    "content": file_content,
                })
            except Exception as e:
                print(f"Error uploading file {file}: {e}")
                continue
        return messages

    def chat(self, file_paths, user_input, use_cache, cache_tag, ttl):
        if not self.file_messages:
            files = file_paths.split('\n')
            self.file_messages = self.upload_files(files=files)

        messages = [
            *self.file_messages,
            {
                "role": "system",
                "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。"
                           "你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，"
                           "种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。",
            },
            *self.conversation_history,
            {
                "role": "user",
                "content": user_input,
            }
        ]

        try:
            if use_cache:
                cache_response = self.get_cache(cache_tag)
                if cache_response:
                    return (cache_response,)

            completion = self.client.chat.completions.create(
                model="moonshot-v1-8k",
                messages=messages,
            )

            assistant_response = completion.choices[0].message.content
            self.conversation_history.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": assistant_response}
            ])

            if use_cache:
                self.set_cache(cache_tag, assistant_response, ttl)

            return (assistant_response,)

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            print(error_message)
            return (error_message,)

    def get_cache(self, cache_tag):
        try:
            response = httpx.get(
                f"{self.client.base_url}/caching",
                headers={"Authorization": f"Bearer {self.client.api_key}"},
                params={"tags": cache_tag}
            )
            response.raise_for_status()
            cache_data = response.json()
            if cache_data and cache_data.get('data'):
                return cache_data['data'][0]['content']
        except Exception as e:
            print(f"Error getting cache: {e}")
        return None

    def set_cache(self, cache_tag, content, ttl):
        try:
            response = httpx.post(
                f"{self.client.base_url}/caching",
                headers={"Authorization": f"Bearer {self.client.api_key}"},
                json={
                    "tags": [cache_tag],
                    "content": content,
                    "ttl": ttl
                }
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Error setting cache: {e}")

# 在 ComfyUI 的节点定义文件中注册这个新节点
NODE_CLASS_MAPPINGS = {
    "FileBasedChatNode": FileBasedChatNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FileBasedChatNode": "File-based Chat"
}