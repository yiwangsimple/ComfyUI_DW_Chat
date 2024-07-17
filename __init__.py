from .groqchat import NODE_CLASS_MAPPINGS as GROQ_CLASS_MAPPINGS
from .groqchat import NODE_DISPLAY_NAME_MAPPINGS as GROQ_DISPLAY_MAPPINGS
from .moonshot_chat_nodes import NODE_CLASS_MAPPINGS as MOONSHOT_CLASS_MAPPINGS
from .moonshot_chat_nodes import NODE_DISPLAY_NAME_MAPPINGS as MOONSHOT_DISPLAY_MAPPINGS
from .SD3LongCaptioner_v2 import NODE_CLASS_MAPPINGS as SD3_V2_CLASS_MAPPINGS
from .SD3LongCaptioner_v2 import NODE_DISPLAY_NAME_MAPPINGS as SD3_V2_DISPLAY_MAPPINGS
from .file_based_chat import NODE_CLASS_MAPPINGS as FILE_CHAT_CLASS_MAPPINGS
from .file_based_chat import NODE_DISPLAY_NAME_MAPPINGS as FILE_CHAT_DISPLAY_MAPPINGS

NODE_CLASS_MAPPINGS = {
    **GROQ_CLASS_MAPPINGS, 
    **MOONSHOT_CLASS_MAPPINGS, 
    **SD3_V2_CLASS_MAPPINGS, 
    **FILE_CHAT_CLASS_MAPPINGS
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **GROQ_DISPLAY_MAPPINGS, 
    **MOONSHOT_DISPLAY_MAPPINGS, 
    **SD3_V2_DISPLAY_MAPPINGS, 
    **FILE_CHAT_DISPLAY_MAPPINGS
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]