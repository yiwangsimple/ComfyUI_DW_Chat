import os
import re

class ErrorLogNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_error_log"
    CATEGORY = "🌙DW"

    def get_error_log(self):
        log_dir = "/Users/weiwei/ComfyUI"
        log_path = os.path.join(log_dir, "comfyui.log")

        if not os.path.exists(log_dir):
            return ("日志目录不存在。",)

        if not os.path.exists(log_path):
            return ("未找到日志文件。",)

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            
            # 使用正则表达式匹配包含 "ERROR"、"Exception"、"Traceback"、"Failed"、"Error" 的行
            error_pattern = re.compile(r'.*(ERROR|Exception|Traceback|Failed|Error).*', re.IGNORECASE)
            error_lines = [line for line in file_content.splitlines() if error_pattern.match(line)]
            
            if error_lines:
                return ("\n".join(error_lines),)
            else:
                return ("未找到错误信息。",)
        except Exception as e:
            return (f"读取日志文件 '{log_path}' 时发生错误：{str(e)}",)

NODE_CLASS_MAPPINGS = {
    "ErrorLogNode": ErrorLogNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ErrorLogNode": "Get error log"
}