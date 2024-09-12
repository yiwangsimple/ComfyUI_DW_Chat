import requests
import json
import os
import asyncio
import aiohttp
import logging
import re
from typing import Tuple, Dict, Any

class PromptEngineeringNode:
    def __init__(self):
        self.model_name = None
        self.base_url = None
        self.api_key = None
        self.is_local = False
        self.ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434/api/generate")
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "input_text": ("STRING", {"multiline": True}),
                "prompt_type": (["通用", "角色扮演", "图像生成", "文本生成", "代码生成", "对话系统", "任务分解", 
                                 "学术写作", "营销文案", "故事创作", "数据分析", "问题解决", "创意思考", "教学指导"], {"default": "通用"}),
                "model_name": ("STRING", {"default": "llama2"}),
                "base_url": ("STRING", {"default": "https://api.openai.com/v1"}),
                "api_key": ("STRING", {"default": ""}),
                "language": (["中文", "英文"], {"default": "中文"}),
                "output_format": (["纯文本", "Markdown", "HTML", "JSON"], {"default": "Markdown"}),
            },
            "optional": {
                "is_local": ("BOOLEAN", {"default": False}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.1}),
                "max_tokens": ("INT", {"default": 2000, "min": 100, "max": 4096}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("response", "history", "prompt")
    FUNCTION = "generate_prompt_sync"
    CATEGORY = "🌙DW/提示词工程"

    def generate_prompt_sync(self, input_text: str, prompt_type: str, model_name: str, base_url: str, api_key: str, 
                             language: str, output_format: str, is_local: bool = True, temperature: float = 0.7, 
                             max_tokens: int = 2000) -> Tuple[str, str, str]:
        return asyncio.run(self.generate_prompt(input_text, prompt_type, model_name, base_url, api_key, 
                                                language, output_format, is_local, temperature, max_tokens))

    async def generate_prompt(self, input_text: str, prompt_type: str, model_name: str, base_url: str, api_key: str, 
                              language: str, output_format: str, is_local: bool = True, temperature: float = 0.7, 
                              max_tokens: int = 2000) -> Tuple[str, str, str]:
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key
        self.is_local = is_local

        system_prompt = self.get_system_prompt(prompt_type, language)
        user_prompt = f"请根据以下输入生成一个结构化的{prompt_type}提示词:\n{input_text}"

        try:
            if self.is_local:
                structured_prompt = await self.local_inference(system_prompt, user_prompt, temperature, max_tokens)
            else:
                structured_prompt = await self.api_inference(system_prompt, user_prompt, temperature, max_tokens)

            formatted_structured_prompt = self.format_output(structured_prompt, output_format)
            
            # 使用结构化提示词生成最终内容
            final_content = await self.generate_final_content(formatted_structured_prompt, input_text, temperature, max_tokens)
            
            # 将历史记录转换为Markdown格式
            history = self.format_history_to_markdown(formatted_structured_prompt, input_text, final_content)

            return (formatted_structured_prompt, history, final_content)
        except Exception as e:
            self.logger.error(f"生成提示词失败: {str(e)}", exc_info=True)
            return (f"错误: 生成提示词失败 - {str(e)}", "", "")
        
    async def generate_final_content(self, structured_prompt: str, user_input: str, temperature: float, max_tokens: int) -> str:
        if self.is_local:
            raw_response = await self.local_inference(structured_prompt, user_input, temperature, max_tokens)
        else:
            raw_response = await self.api_inference(structured_prompt, user_input, temperature, max_tokens)
        
        # 提取 <output></output> 标签内的内容
        output_content = self.extract_output_content(raw_response)
        return output_content

    def extract_output_content(self, text: str) -> str:
        pattern = r'<output>(.*?)</output>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # 移除结构标题和标签
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if not line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '<', '>')):
                    if ':' in line:
                        _, text = line.split(':', 1)
                        cleaned_lines.append(text.strip())
                    else:
                        cleaned_lines.append(line)
            
            # 合并相邻的短句
            merged_lines = []
            current_line = ""
            for line in cleaned_lines:
                if len(current_line) + len(line) < 100:  # 可以调整这个数值来控制合并的程度
                    current_line += " " + line if current_line else line
                else:
                    if current_line:
                        merged_lines.append(current_line)
                    current_line = line
            if current_line:
                merged_lines.append(current_line)
            
            return '\n\n'.join(merged_lines)
        else:
            self.logger.warning("未找到 <output> 标签，返回空字符串")
            return ""

    def get_system_prompt(self, prompt_type: str, language: str) -> str:
        base_prompt = f"""
        你是一个专业的提示词工程师,精通LangGPT结构化提示词方法论。你的任务是根据用户输入的简单描述,生成一个结构化、详细的{language}提示词。请严格按照以下结构生成提示词:

        1. 角色设定 (Role): 定义AI助手的身份和专业背景。
        2. 背景信息 (Background): 提供任务相关的上下文或背景。
        3. 任务目标 (Task): 明确指出要完成的具体任务。
        4. 示例 (Examples): 如果需要,提供一个简短的示例说明。
        5. 评估标准 (Evaluation): 说明如何评判输出的质量。
        6. 命令词 (Commands): 使用明确的指令性语言。
        7. 工作流程 (Workflow): 如果任务复杂,提供步骤分解。
        8. 个性化 (Personalization): 根据需要调整AI的语气和风格。
        9. 约束条件 (Constraints): 列出任何限制或约束条件。

        对于视觉相关的提示词,请综合描述构图、颜色、风格和光照等元素,不要使用单独的标签,而是将它们整合成连贯的段落。

        请确保生成的提示词结构清晰,内容丰富,能够指导AI生成高质量的内容。使用Markdown格式来组织提示词的结构,并使用XML标签来标记关键部分。
        """
        
        type_specific_prompts = {
            "通用": "",
            "角色扮演": "特别注意角色设定的细节,包括性格特征、说话方式等。使用<character></character>标签定义角色特征。",
            "图像生成": "详细描述视觉元素,如构图、色彩、风格、光影等。使用<visual></visual>标签包裹关键视觉描述。考虑使用<composition></composition>, <color></color>, <style></style>等子标签。",
            "文本生成": "明确指出文本的类型、结构、风格、语气和目标读者。使用<style></style>标签定义文本风格,<audience></audience>标签定义目标读者。",
            "代码生成": "指定编程语言、功能需求、代码风格和性能考虑。使用<code></code>标签包裹代码示例或要求,<language></language>标签指定编程语言。",
            "对话系统": "定义对话的目的、语气、个性化特征和上下文理解要求。使用<dialogue></dialogue>标签模拟对话流程,<context></context>标签定义上下文信息。",
            "任务分解": "将复杂任务分解为多个子任务或步骤。使用<step></step>标签定义每个步骤,<subtask></subtask>标签定义子任务。",
            "学术写作": "注重学术格式、引用规范和专业术语的使用。使用<citation></citation>标签标记引用,<terminology></terminology>标签定义专业术语。",
            "营销文案": "强调吸引力、说服力和号召性用语。使用<headline></headline>标签定义标题,<cta></cta>标签定义行动号召。",
            "故事创作": "关注情节发展、角色塑造和场景描述。使用<plot></plot>标签概述情节,<character></character>标签描述角色,<setting></setting>标签描述场景。",
            "数据分析": "明确数据源、分析方法和预期洞察。使用<data></data>标签描述数据集,<method></method>标签定义分析方法。",
            "问题解决": "清晰定义问题,提供背景信息,并指导思考过程。使用<problem></problem>标签描述问题,<solution></solution>标签概述解决方案。",
            "创意思考": "鼓励发散思维和创新想法。使用<idea></idea>标签标记创意点,<inspiration></inspiration>标签提供灵感来源。",
            "教学指导": "明确学习目标、教学方法和评估标准。使用<objective></objective>标签定义学习目标,<method></method>标签描述教学方法。"
        }
        
        return base_prompt + type_specific_prompts.get(prompt_type, "")

    async def local_inference(self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str:
        prompt = f"{system_prompt}\n\n用户: {user_prompt}\n\n助手:"
        
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.ollama_url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['response']
                else:
                    raise Exception(f"Ollama 调用失败,状态码 {response.status}")

    async def api_inference(self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/chat/completions", headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    raise Exception(f"API 调用失败,状态码 {response.status}")

    def format_output(self, text: str, output_format: str) -> str:
        if output_format == "纯文本":
            return text
        elif output_format == "Markdown":
            return text
        elif output_format == "HTML":
            # 这里可以添加Markdown到HTML的转换逻辑
            html = text.replace("\n", "<br>")
            return f"<div>{html}</div>"
        elif output_format == "JSON":
            # 尝试将文本解析为JSON结构
            try:
                json_data = json.loads(text)
                return json.dumps(json_data, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                self.logger.warning("无法将文本解析为JSON,返回原始文本")
                return text

    def format_history_to_markdown(self, system_content: str, user_content: str, assistant_content: str) -> str:
        markdown_history = f"""
## 系统消息

{system_content}

## 用户输入

{user_content}

## 助手回复

{assistant_content}
"""
        return markdown_history.strip()

NODE_CLASS_MAPPINGS = {
    "PromptEngineeringNode": PromptEngineeringNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptEngineeringNode": "提示词工程节点"
}