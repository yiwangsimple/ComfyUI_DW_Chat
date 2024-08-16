import time
from functools import wraps

import execution
import server

def time_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time
    return wrapper

class ExecutionTime:
    CATEGORY = "DW-Utils/Debug"

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}

    RETURN_TYPES = ("STRING",)  # 添加字符串输出接口
    RETURN_NAMES = ("execution_time",)
    FUNCTION = "process"

    def process(self):
        return ("",)  # 返回空字符串，实际的总执行时间将在 swizzle_send_sync 中设置

    @staticmethod
    def display_total_execution_time(total_time):
        formatted_time = f"{total_time:.2f}s"
        print(f"Total Execution Time: {formatted_time}")
        return formatted_time

# 假设 `execute` 是 `execution` 模块中存在的一个方法，可以替代 `recursive_execute`
origin_execute = execution.execute

@time_execution
def timed_execute(*args, **kwargs):
    return origin_execute(*args, **kwargs)

def swizzle_origin_execute(server, prompt, outputs, current_item, extra_data, executed, prompt_id, outputs_ui, object_storage):
    unique_id = current_item

    # 尝试访问 class_type（需要根据实际情况调整）
    try:
        class_type = "Unknown"  # 默认值
       
    except AttributeError as e:
        print(f"Error: Failed to access class_type for unique_id {unique_id}: {e}")
        return None

    last_node_id = server.last_node_id
    
    result, execution_time = timed_execute(server, prompt, outputs, current_item, extra_data, executed, prompt_id, outputs_ui, object_storage)
    
    if server.client_id is not None and last_node_id != server.last_node_id:
        server.send_sync(
            "DW-Utils.ExecutionTime.executed",
            {"node": unique_id, "prompt_id": prompt_id, "execution_time": int(execution_time * 1000)},
            server.client_id
        )
    print(f"#{unique_id} [{class_type}]: {execution_time:.2f}s")
    
    return result

execution.execute = swizzle_origin_execute

origin_func = server.PromptServer.send_sync

def swizzle_send_sync(self, event, data, sid=None):
    if event == "execution_start":
        self.execution_start_time = time.perf_counter()

    origin_func(self, event=event, data=data, sid=sid)

    if event == "execution_complete" and sid is not None:
        execution_time = time.perf_counter() - self.execution_start_time
        new_data = data.copy()
        new_data['total_execution_time'] = int(execution_time * 1000)
        origin_func(
            self,
            event="DW-Utils.ExecutionTime.execution_complete",
            data=new_data,
            sid=sid
        )
        formatted_time = ExecutionTime.display_total_execution_time(execution_time)
        server.send_sync(
            "DW-Utils.ExecutionTime.total_time",
            {"total_execution_time": formatted_time},
            sid
        )

server.PromptServer.send_sync = swizzle_send_sync

NODE_CLASS_MAPPINGS = {
    "ExecutionTime": ExecutionTime
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExecutionTime": "Execution Time"
}