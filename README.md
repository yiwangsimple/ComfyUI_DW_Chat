# comfy-groqchat
Updated image backpropagation nodes based on Google's open-source PaliGemma vision model. The model used in the node is a fine-tuned version of gokayfem's big brother, special thanks for that! Content generation with open source models in comfyui via graq api implementation.

# Usage:
2024-07-27  
在groqchat节点中新增了reset conversation参数，值为True时，即可开启多轮对话功能；新增了prompt_extractor.py节点，分来分离文本中的正负向提示词。
![](image/demo03.png)

2024-07-24  
1.基于groq API的节点，新增了llama3.1模型的支持。
2.优化所有节点的分类，新增moondream2的图片反推节点dwimage2.py，模型支持手动下载到./ComfyUI/models/LLavacheckpoints/files_for_moondream2目录下（所有文件放在这个文件夹下）。 模型地址：https://huggingface.co/vikhyatk/moondream2/tree/main

2024-07-14  
新增了SD3LongCaptionerV2这个图像反推节点的模型加载和存储目录，考虑到模型偏大的问题，可以手动从huggingface上下载模型放到ComfyUl/models/LLavacheckpoints/files_for_sd3_long_captioner_v2这个目录下，模型地址https://huggingface.co/gokaygokay/sd3-long-captioner-v2

再次更新了基于kimi API的文件对话功能的file_based_chat节点，能实现低配的知识库功能，上传文件格式支持pdf、doc、xlsx、ppt、txt、图片等。具体应用示例，可以上传知识库中的”常见报错问题(文档可在库中获得，来源K佬)”，来解决部分报错问题
![](image/demo02.png)
新更新了对 kimi api的支持，包括“Moonshot Single Chat”和“Moonshot Multi Chat”两个节点，分别支持单轮或多轮对话。API申请地址 https://platform.moonshot.cn/console/info
单轮对话，如下所示：
![](image/single.png)
多轮对话：
![](image/multi.png)

Groq nodes are based on the groq cloud API.The following four models are currently supported.
* gemma-7b-it
* llama3-70b-8192
* mixtral-8x7b-32768
* llama3-8b-8192

The API was requested through https://console.groq.com/keys, which had not launched a paid plan as of the time of publication. Fill the api key into the "config.json" file.
However, there are corresponding restrictions, as shown below:
![](image/limits.png)
____
## Example:
![](image/workflow.png)
The use of nodes enables the generation of positive and negative cues in 2 seconds through specific cues.
![](image/prompt_workflow.png)
Picture with workflow
____
##Statement：
The GroqChat node follows the MIT license agreement, and some of the functional code comes from other open source projects. Thanks to the original authors. For commercial use, please refer to the original project license agreement for authorization.Thanks also to Google's open source PaliGemma model.

