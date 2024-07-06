# comfy-groqchat
Updated image backpropagation nodes based on Google's open-source PaliGemma vision model. The model used in the node is a fine-tuned version of gokayfem's big brother, special thanks for that! Content generation with open source models in comfyui via graq api implementation.

# Usage:
PaliGemmaPixelProse image backpropagation node.
![](demo01.png)
The following four models are currently supported.
* gemma-7b-it
* llama3-70b-8192
* mixtral-8x7b-32768
* llama3-8b-8192

The API was requested through https://console.groq.com/keys, which had not launched a paid plan as of the time of publication. Fill the api key into the "config.json" file.
However, there are corresponding restrictions, as shown below:
![](limits.png)
____
## Example:
![](workflow.png)
The use of nodes enables the generation of positive and negative cues in 2 seconds through specific cues.
![](prompt_workflow.png)
Picture with workflow
____
##Statement：
The GroqChat node follows the MIT license agreement, and some of the functional code comes from other open source projects. Thanks to the original authors. For commercial use, please refer to the original project license agreement for authorization.Thanks also to Google's open source PaliGemma model.

