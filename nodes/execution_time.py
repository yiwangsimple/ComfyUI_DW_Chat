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
    CATEGORY = "TyDev-Utils/Debug"

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "process"

    def process(self):
        return ()

origin_recursive_execute = execution.recursive_execute

@time_execution
def timed_recursive_execute(*args, **kwargs):
    return origin_recursive_execute(*args, **kwargs)

def swizzle_origin_recursive_execute(server, prompt, outputs, current_item, extra_data, executed, prompt_id, outputs_ui, object_storage):
    unique_id = current_item
    class_type = prompt[unique_id]['class_type']
    last_node_id = server.last_node_id
    
    result, execution_time = timed_recursive_execute(server, prompt, outputs, current_item, extra_data, executed, prompt_id, outputs_ui, object_storage)
    
    if server.client_id is not None and last_node_id != server.last_node_id:
        server.send_sync(
            "TyDev-Utils.ExecutionTime.executed",
            {"node": unique_id, "prompt_id": prompt_id, "execution_time": int(execution_time * 1000)},
            server.client_id
        )
    print(f"#{unique_id} [{class_type}]: {execution_time:.2f}s")
    
    return result

execution.recursive_execute = swizzle_origin_recursive_execute

origin_func = server.PromptServer.send_sync

def swizzle_send_sync(self, event, data, sid=None):
    if event == "execution_start":
        self.execution_start_time = time.perf_counter()

    origin_func(self, event=event, data=data, sid=sid)

    if event == "executing" and data and data.get("node") is None and sid is not None:
        execution_time = time.perf_counter() - self.execution_start_time
        new_data = data.copy()
        new_data['execution_time'] = int(execution_time * 1000)
        origin_func(
            self,
            event="TyDev-Utils.ExecutionTime.execution_end",
            data=new_data,
            sid=sid
        )

server.PromptServer.send_sync = swizzle_send_sync

NODE_CLASS_MAPPINGS = {
    "ExecutionTime": ExecutionTime
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExecutionTime": "Execution Time"
}