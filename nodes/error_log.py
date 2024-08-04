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
        # 获取当前文件的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 向上导航三级目录到ComfyUI根目录
        comfyui_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        
        # 使用正则表达式匹配日志文件
        log_pattern = re.compile(r'comfyui.*\.log')
        log_files = [f for f in os.listdir(comfyui_root) if log_pattern.match(f)]
        
        if not log_files:
            return ("未找到日志文件。",)
        
        # 使用最新的日志文件
        latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(comfyui_root, f)))
        log_path = os.path.join(comfyui_root, latest_log)

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