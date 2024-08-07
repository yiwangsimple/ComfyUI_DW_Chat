import os
import json
import folder_paths
from server import PromptServer
from aiohttp import web

print("GitHub Button extension Python module loaded")

class GithubLinkNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}
    
    RETURN_TYPES = ()
    FUNCTION = "github_link"
    CATEGORY = "utils"

    def github_link(self):
        return {}

def load_extension_node_map():
    json_path = os.path.join(folder_paths.base_path, "custom_nodes", "Comfyui-Manager",  "extension-node-map.json")
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    return {}

def get_github_url(repo_path):
    if not repo_path.startswith(('http://', 'https://')):
        return None
    parts = repo_path.split('/')
    if 'github.com' in parts:
        github_index = parts.index('github.com')
        return '/'.join(parts[:github_index+3])
    return None

def get_git_repo_url(repo_path):
    git_config_path = os.path.join(repo_path, '.git', 'config')
    if os.path.exists(git_config_path):
        with open(git_config_path, 'r') as f:
            config = f.read()
            for line in config.splitlines():
                if line.strip().startswith('url ='):
                    return line.split('=')[1].strip()
    return None

def initialize_github_links():
    github_links = {}
    extension_node_map = load_extension_node_map()

    # Process nodes from extension-node-map.json
    for url, nodes_info in extension_node_map.items():
        github_url = get_github_url(url)
        if github_url:
            for node in nodes_info[0]:
                if node not in github_links:
                    github_links[node] = github_url

    # Process custom nodes not in extension-node-map.json
    custom_nodes_dir = os.path.join(folder_paths.base_path, "custom_nodes")
    if os.path.exists(custom_nodes_dir):
        for node_folder in os.listdir(custom_nodes_dir):
            node_path = os.path.join(custom_nodes_dir, node_folder)
            if os.path.isdir(node_path):
                git_url = get_git_repo_url(node_path)
                if git_url:
                    github_url = get_github_url(git_url)
                    if github_url:
                        github_links[node_folder] = github_url

    # Save the GitHub links to a JSON file in the same directory as this script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    web_dir = os.path.join(script_dir, "web")
    if not os.path.exists(web_dir):
        os.makedirs(web_dir)
    json_path = os.path.join(web_dir, "github_links.json")
    with open(json_path, 'w') as f:
        json.dump(github_links, f, indent=4)

    return github_links

async def api_get_github_links(request):
    github_links = initialize_github_links()
    return web.json_response(github_links)

NODE_CLASS_MAPPINGS = {
    "GithubLinkNode": GithubLinkNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GithubLinkNode": "GitHub Link"
}

WEB_DIRECTORY = "web"

@PromptServer.instance.routes.get("/github_btn/get_github_links")
async def get_github_links_route(request):
    print("Received request for all GitHub links")
    result = await api_get_github_links(request)
    print(f"Returning result: {result}")
    return result

print("GitHub Button extension API route registered")

# Ensure github_links.json is created when the server starts
initialize_github_links()