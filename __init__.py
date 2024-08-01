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
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "load_api_key"]