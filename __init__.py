import os
from .api_utils import load_api_key

from .nodes.groqchat import NODE_CLASS_MAPPINGS as GROQ_CLASS_MAPPINGS
from .nodes.groqchat import NODE_DISPLAY_NAME_MAPPINGS as GROQ_DISPLAY_MAPPINGS
from .nodes.moonshot_chat_nodes import NODE_CLASS_MAPPINGS as MOONSHOT_CLASS_MAPPINGS
from .nodes.moonshot_chat_nodes import NODE_DISPLAY_NAME_MAPPINGS as MOONSHOT_DISPLAY_MAPPINGS
from .nodes.SD3LongCaptioner_v2 import NODE_CLASS_MAPPINGS as SD3_V2_CLASS_MAPPINGS
from .nodes.SD3LongCaptioner_v2 import NODE_DISPLAY_NAME_MAPPINGS as SD3_V2_DISPLAY_MAPPINGS
from .nodes.file_based_chat import NODE_CLASS_MAPPINGS as FILE_CHAT_CLASS_MAPPINGS
from .nodes.file_based_chat import NODE_DISPLAY_NAME_MAPPINGS as FILE_CHAT_DISPLAY_MAPPINGS
from .nodes.dwimage2 import NODE_CLASS_MAPPINGS as MOONDREAM2_V2_NODE_CLASS_MAPPINGS
from .nodes.dwimage2 import NODE_DISPLAY_NAME_MAPPINGS as MOONDREAM2_V2_NODE_DISPLAY_NAME_MAPPINGS
from .nodes.prompt_extractor import NODE_CLASS_MAPPINGS as PROMPT_EXTRACTOR_CLASS_MAPPINGS
from .nodes.prompt_extractor import NODE_DISPLAY_NAME_MAPPINGS as PROMPT_EXTRACTOR_DISPLAY_MAPPINGS
from .nodes.sdprompt_agent import NODE_CLASS_MAPPINGS as SD_PROMPT_AGENT_CLASS_MAPPINGS
from .nodes.sdprompt_agent import NODE_DISPLAY_NAME_MAPPINGS as SD_PROMPT_AGENT_DISPLAY_NAME_MAPPINGS
from .nodes.ollama_prompt_extractor import NODE_CLASS_MAPPINGS as OLLAMA_PROMPT_EXTRACTOR_CLASS_MAPPINGS
from .nodes.ollama_prompt_extractor import NODE_DISPLAY_NAME_MAPPINGS as OLLAMA_PROMPT_EXTRACTOR_DISPLAY_MAPPINGS
from .nodes.deepseek_translater import NODE_CLASS_MAPPINGS as DEEPSEEK_TRANSLATOR_CLASS_MAPPINGS
from .nodes.deepseek_translater import NODE_DISPLAY_NAME_MAPPINGS as DEEPSEEK_TRANSLATOR_DISPLAY_MAPPINGS
from .nodes.deepseek_chat import NODE_CLASS_MAPPINGS as DEEPSEEK_CHAT_CLASS_MAPPINGS
from .nodes.deepseek_chat import NODE_DISPLAY_NAME_MAPPINGS as DEEPSEEK_CHAT_DISPLAY_MAPPINGS
from .nodes.error_log import NODE_CLASS_MAPPINGS as ERROR_LOG_CLASS_MAPPINGS
from .nodes.error_log import NODE_DISPLAY_NAME_MAPPINGS as ERROR_LOG_DISPLAY_MAPPINGS

# 导入执行时间插件
from .nodes.execution_time import NODE_CLASS_MAPPINGS as EXECUTION_TIME_CLASS_MAPPINGS
from .nodes.execution_time import NODE_DISPLAY_NAME_MAPPINGS as EXECUTION_TIME_DISPLAY_MAPPINGS

#导入gemmma2相关节点
from .nodes.gemma_node import NODE_CLASS_MAPPINGS as GEMMA_NODE_CLASS_MAPPINGS
from .nodes.gemma_node import NODE_DISPLAY_NAME_MAPPINGS as GEMMA_NODE_DISPLAY_MAPPINGS
from .nodes.gemma2prompt import NODE_CLASS_MAPPINGS as GEMMA2_PROMPT_CLASS_MAPPINGS
from .nodes.gemma2prompt import NODE_DISPLAY_NAME_MAPPINGS as GEMMA2_PROMPT_DISPLAY_MAPPINGS

# 定义执行时间统计函数
def load_javascript(web_directory):
    js_file_path = os.path.join(web_directory, "executionTime.js")
    if os.path.exists(js_file_path):
        with open(js_file_path, "r") as js_file:
            javascript = js_file.read()
        return javascript
    return None

# 确保在 NODE_CLASS_MAPPINGS 定义之前添加这行
WEB_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web")

NODE_CLASS_MAPPINGS = {
    **GROQ_CLASS_MAPPINGS, 
    **MOONSHOT_CLASS_MAPPINGS, 
    **SD3_V2_CLASS_MAPPINGS, 
    **FILE_CHAT_CLASS_MAPPINGS,
    **MOONDREAM2_V2_NODE_CLASS_MAPPINGS,
    **PROMPT_EXTRACTOR_CLASS_MAPPINGS,
    **SD_PROMPT_AGENT_CLASS_MAPPINGS,
    **OLLAMA_PROMPT_EXTRACTOR_CLASS_MAPPINGS,
    **DEEPSEEK_TRANSLATOR_CLASS_MAPPINGS,
    **DEEPSEEK_CHAT_CLASS_MAPPINGS,
    **ERROR_LOG_CLASS_MAPPINGS, 
    **EXECUTION_TIME_CLASS_MAPPINGS,  # 添加执行时间插件的类映射
    **GEMMA2_PROMPT_CLASS_MAPPINGS,  # 添加 Gemma2PromptNode 的类映射
    **GEMMA_NODE_CLASS_MAPPINGS,  # 添加 GemmaNode 的类映射
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **GROQ_DISPLAY_MAPPINGS, 
    **MOONSHOT_DISPLAY_MAPPINGS, 
    **SD3_V2_DISPLAY_MAPPINGS, 
    **FILE_CHAT_DISPLAY_MAPPINGS,
    **MOONDREAM2_V2_NODE_DISPLAY_NAME_MAPPINGS,
    **PROMPT_EXTRACTOR_DISPLAY_MAPPINGS,
    **SD_PROMPT_AGENT_DISPLAY_NAME_MAPPINGS,
    **OLLAMA_PROMPT_EXTRACTOR_DISPLAY_MAPPINGS,
    **DEEPSEEK_TRANSLATOR_DISPLAY_MAPPINGS,
    **DEEPSEEK_CHAT_DISPLAY_MAPPINGS,
    **ERROR_LOG_DISPLAY_MAPPINGS,
    **EXECUTION_TIME_DISPLAY_MAPPINGS,  # 添加执行时间插件的显示名称映射
    **GEMMA2_PROMPT_DISPLAY_MAPPINGS,  # 添加 Gemma2PromptNode 的显示名称映射
    **GEMMA_NODE_DISPLAY_MAPPINGS,  # 添加 GemmaNode 的显示名称映射
}


WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "load_api_key"]