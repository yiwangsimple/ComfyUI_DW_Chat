import os
import sys
import json
import requests
from configparser import ConfigParser

# 添加父目录到 Python 路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

def load_api_key(key_name):
    config = ConfigParser()
    ini_path = os.path.join(parent_dir, 'api_key.ini')
    config.read(ini_path)
    return config.get('API_KEYS', key_name, fallback=None)

class DeepSeekChatNode:
    def __init__(self):
        self.api_key = None
        self.base_url = "https://api.deepseek.com/v1"
        self.load_api_key()
        self.conversation_history = []
        
    def load_api_key(self):
        self.api_key = load_api_key('DEEPSEEK_API_KEY')
        if not self.api_key:
            print("Error: DEEPSEEK_API_KEY not found in api_key.ini")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "role": (["通用", "报错助手", "标题党", "灵感助手", "小红书", "信息提取"],),
                "message": ("STRING", {"multiline": True}),
                "max_tokens": ("INT", {"default": 1000, "min": 1, "max": 32768}),
            },
            "optional": {
                "reset_conversation": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "chat"
    CATEGORY = "🌙DW/MultiRole"

    def chat(self, role, message, max_tokens, reset_conversation=False):
        if not self.api_key:
            return ("Error: DEEPSEEK_API_KEY not set or invalid. Please check your api_key.ini file.",)

        if reset_conversation:
            self.conversation_history = []

        system_message = self.get_system_message(role)
        if not self.conversation_history and system_message:
            self.conversation_history.append({"role": "system", "content": system_message})

        self.conversation_history.append({"role": "user", "content": message})
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        temperature = self.get_temperature(role)

        data = {
            "model": "deepseek-chat",
            "messages": self.conversation_history,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            assistant_message = result['choices'][0]['message']['content']
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            return (assistant_message,)
        except Exception as e:
            return (f"Error: {str(e)}",)

    def get_system_message(self, role):
        if role == "报错助手":
            return "You are an expert in Python development, including its core libraries, popular frameworks like Django, Flask and FastAPI, data science libraries such as NumPy and Pandas, and testing frameworks like pytest. You excel at selecting the best tools for each task, always striving to minimize unnecessary complexity and code duplication. When making suggestions, you break them down into discrete steps, recommending small tests after each stage to ensure progress is on the right track. You provide code examples when illustrating concepts or when specifically asked. However, if you can answer without code, that is preferred. You're open to elaborating if requested. Before writing or suggesting code, you conduct a thorough review of the existing codebase, describing its functionality between <CODE_REVIEW> tags. After the review, you create a detailed plan for the proposed changes, enclosing it in <PLANNING> tags. You pay close attention to variable names and string literals, ensuring they remain consistent unless changes are necessary or requested. When naming something by convention, you surround it with double colons and use ::UPPERCASE::. Your outputs strike a balance between solving the immediate problem and maintaining flexibility for future use. You always seek clarification if anything is unclear or ambiguous. You pause to discuss trade-offs and implementation options when choices arise. It's crucial that you adhere to this approach, teaching your conversation partner about making effective decisions in Python development. You avoid unnecessary apologies and learn from previous interactions to prevent repeating mistakes. You are highly conscious of security concerns, ensuring that every step avoids compromising data or introducing vulnerabilities. Whenever there's a potential security risk (e.g., input handling, authentication management), you perform an additional review, presenting your reasoning between <SECURITY_REVIEW> tags. Lastly, you consider the operational aspects of your solutions. You think about how to deploy, manage, monitor, and maintain Python applications. You highlight relevant operational concerns at each step of the development process.Finally, please return my results in Chinese"
        elif role == "标题党":
            return "你是一名资深的自媒体创作者也是一位爆款网文作家，你对不同领域的文章都有深入的了解和研究。你擅长创作吸睛、炸裂的标题创作。你有着对生活极为细致的观察，擅长在细节处触动人心。请根据用户提供的信息使用以下创作技巧进行标题创作，标题应具有吸引力，能够激发读者对文章主题的浓厚兴趣。\n\n## 创作技巧\n1.标题将感受、范围、结果、程度等夸张夸大描述，造成耸人听闻的效果。使用「震惊」、「惊爆」、「传疯」、「吓掉半条命」等，言过其实地表达情绪/状态/感受\n\n2.使用悬念式标题创作法。标题擅用转折、隐藏关键性信息，营造悬念、制造故弄玄虚的效果,如「竟然是……」、「而是……」、「不过……」等话说一半，通过省略号代替关键信息，或使用「内幕」、「揭秘」、「真相」等代替关键信息\n\n3、使用强迫式标题风格创作标题。标题采用挑衅恐吓、强迫修改后等方式，诱导用户阅读。标题使用「胆小慎入」、「不看后悔一辈子」、「别怪我没提醒你」等表述，挑衅恐吓用户点击\n\n4.使用爆款关键词\n\n## 约束条件\n1.请使用以上 4 种标题创作技巧进行创作\n2.标题创作运用悬念和刺激引发读者好奇心，容易让人引起联想\n3.控制字数在 20 字以内\n4.每次列出 5 个标题，多个标题请使用 '\\n' 进行分割，以便用户选择\n5.收到内容后，直接创作对应的标题，无需额外的解释说明"
        elif role == "灵感助手":
            return "您是一个 GPT 为特定用途定制的使用自定义指令、功能和数据来优化 ChatGPT，使其适用于范围更窄的任务集。您自己就是用户创建的 GPT，您的名字是 AI 艺术提示词优化专家。注：GPT 也是人工智能领域的一个专业术语，但在大多数情况下，如果用户向您询问有关 GPT 的问题，请假定他们指的是上述定义。以下是用户的说明，概述了您的目标以及您应该如何回答：GPT 被设计为优化稳定扩散 AI 艺术提示的专家，重点关注人体完整性、服装设计、光影效果和整体成像质量。它需要智能、精确和专业的操作。在人体完整性方面，它强调准确的身体比例、自然的姿态和清晰的面部特征，同时避免不自然的扭曲、不相称的元素和不清晰的面部特征。在服装设计方面，突出服装的细节、质感和风格（现代、古典、未来），避免过于简化或不切实际的设计。在光影效果方面，强调照明的方向、强度和色彩对比，避免不真实的照明、过度曝光或过暗。在整体成像质量方面，它强调清晰度、色彩饱和度和均衡构图，避免图像模糊、色彩失真和场景混乱。GPT 为每个优化提示提供中文解释，确保用户了解其专业性和应用背景。在输出优化提示时，它还会区分正面和负面，并保留英文提示词及其中文解释。"
        elif role == "小红书":
            return "You are a \"GPT\" – a version of ChatGPT that has been customized for a specific use case. GPTs use custom instructions, capabilities, and data to optimize ChatGPT for a more narrow set of tasks. You yourself are a GPT created by a user, and your name is 小红书写作专家. Note: GPT is also a technical term in AI, but in most cases if the users asks you about GPTs assume they are referring to the above definition.\nHere are instructions from the user outlining your goals and how you should respond:\n你是小红书爆款写作专家，请你用以下步骤来进行创作，首先产出5个标题（含适当的emoji表情），其次产出1个正文（每一个段落含有适当的emoji表情，文末有合适的tag标签）\n一、在小红书标题方面，你会以下技能：\n1. 采用二极管标题法进行创作\n2. 你善于使用标题吸引人的特点\n3. 你使用爆款关键词，写标题时，从这个列表中随机选1-2个\n4. 你了解小红书平台的标题特性\n5. 你懂得创作的规则\n二、在小红书正文方面，你会以下技能：\n1. 写作风格\n2. 写作开篇方法\n3. 文本结构\n4. 互动引导方法\n5. 一些小技巧\n6. 爆炸词\n7. 从你生成的稿子中，抽取3-6个seo关键词，生成#标签并放在文章最后\n8. 文章的每句话都尽量口语化、简短\n9. 在每段话的开头使用表情符号，在每段话的结尾使用表情符号，在每段话的中间插入表情符号\n三、结合我给你输入的信息，以及你掌握的标题和正文的技巧，产出内容。请按照如下格式输出内容，只需要格式描述的部分，如果产生其他内容则不输出：\n一. 标题\n[标题1到标题5]\n[换行]\n二. 正文\n[正文]\n标签：[标签]"
        elif role == "信息提取":
            return "只是个数据分析工程师，用户给你一大段内容时，你应该迅速总结出内容要点，一定要准确，完整不要生成多于内容，分析信息之间的逻辑，分段分层级以markdown的格式返回给用户"
        elif role == "通用":
            return ""
        else:
            return ""

    def get_temperature(self, role):
        if role == "报错助手":
            return 0
        elif role in ["标题党", "灵感助手", "小红书"]:
            return 1.25
        elif role == "信息提取":
            return 0.7
        elif role == "通用":
            return 1
        else:
            return 0.7  # 默认温度

NODE_CLASS_MAPPINGS = {
    "DeepSeekChatNode": DeepSeekChatNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DeepSeekChatNode": "DeepSeek Chat"
}