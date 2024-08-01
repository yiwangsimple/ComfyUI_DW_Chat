import os
import glob

class ErrorLogNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_error_log"
    CATEGORY = "🌙DW"

    def get_error_log(self):
        possible_log_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "comfyui.log"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "comfyui.log"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "*.log"),
        ]

        log_content = "未找到日志文件。搜索的位置：\n"
        
        for path in possible_log_paths:
            log_content += f"- {path}\n"
            if "*" in path:
                matching_files = glob.glob(path)
                if matching_files:
                    path = matching_files[0]  # 使用找到的第一个日志文件
            
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    log_lines = file_content.splitlines()[-1000:]  # 只返回最后的1000行
                    return ("\n".join(log_lines),)
                except Exception as e:
                    return (f"读取日志文件 '{path}' 时发生错误：{str(e)}",)

        return (log_content,)

NODE_CLASS_MAPPINGS = {
    "ErrorLogNode": ErrorLogNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ErrorLogNode": "Get error log"
}