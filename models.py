#!/usr/bin/python3

from langchain_openai import ChatOpenAI

class Tongyi(ChatOpenAI):
  def __init__(self, configs, tags = None):
    super(Tongyi, self).__init__(
      api_key = configs.dashscope_api,
      base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1",
      model_name = configs.model_name,
      top_p = 0.8,
      temperature = 0.7,
      presence_penalty = 1.5,
      extra_body = {
        "top_k": 20,
        "enable_thinking": False
      },
      tags = tags
    )

class Qwen3_vllm(ChatOpenAI):
  def __init__(self, configs, tags = None):
    super(Qwen3_vllm, self).__init__(
      api_key = 'token-abc123',
      base_url = configs.vllm_host,
      model_name = 'Qwen/Qwen3-8B', #"Qwen/Qwen3-8B", # 'Qwen/Qwen3-14B' 'Qwen/Qwen3-32B-FP8'
      temperature = 0.0, #0.7,
      #top_p = 0.8,
      presence_penalty = 1.5,
      extra_body = {
        #"top_k": 20,
        "chat_template_kwargs": {"enable_thinking": configs.thinking},
      },
      tags = tags
    )
