import os

class ErrorLogNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_error_log"
    CATEGORY = "🌙DW"

    def get_error_log(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        log_dir = os.path.join(base_dir, "..", "..", "comfyui")
        log_path = os.path.join(log_dir, "comfyui.log")

        debug_info = f"Base Directory: {base_dir}\nLog Directory: {log_dir}\nLog Path: {log_path}\n"

        if not os.path.exists(log_dir):
            return (f"{debug_info}日志目录不存在。",)

        if not os.path.exists(log_path):
            return (f"{debug_info}未找到日志文件。",)

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            log_lines = file_content.splitlines()[-1000:]  # 只返回最后的1000行
            return ("\n".join(log_lines),)
        except Exception as e:
            return (f"{debug_info}读取日志文件 '{log_path}' 时发生错误：{str(e)}",)

NODE_CLASS_MAPPINGS = {
    "ErrorLogNode": ErrorLogNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ErrorLogNode": "Get error log"
}