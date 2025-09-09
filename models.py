#!/usr/bin/python3

from os import environ
import json
import json_repair
import random
import string
from langchain import hub
from transformers import AutoTokenizer
from langchain_community.llms import HuggingFaceTextGenInference
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFacePipeline
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents.format_scratchpad.tools import format_to_tool_messages
from langchain.agents.output_parsers import ToolsAgentOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, ToolMessage
from configs import huggingface_token, tgi_host

class Qwen2_5(ChatHuggingFace):
  def __init__(self,):
    environ['HUGGINGFACEHUB_API_TOKEN'] = huggingface_token
    super(ChatHuggingFace, self).__init__(
      llm = HuggingFaceTextGenInference(
        inference_server_url = tgi_host,
        top_p = 0.8,
        temperature = 0.8,
        do_sample = False
      ),
      tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct'),
      verbose = True
    )

'''
class Qwen2_5(ChatHuggingFace):
  def __init__(self,):
    environ['HUGGINGFACEHUB_API_TOKEN'] = huggingface_token
    super(ChatHuggingFace, self).__init__(
      llm = HuggingFacePipeline.from_model_id(
        model_id = "Qwen/Qwen2.5-7B-Instruct-1M",
        task = "text-generation",
        pipeline_kwargs = {'do_sample': True}
      ),
      tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct-1M'),
      verbose = True
    )
'''

if __name__ == "__main__":
  from langchain_core.tools import tool
  from langchain.agents import AgentExecutor, create_tool_calling_agent

  @tool
  def add(a: int, b: int) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b

  @tool
  def multiply(a: int, b: int) -> int:
    """Multiplies a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b

  chat_model = Llama3_2()
  tools = [add, multiply]
  if False:
    prompt = hub.pull("hwchase17/openai-functions-agent")
    agent = create_tool_calling_agent(chat_model, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    response = agent_executor.invoke({"input": "What is 3 * 12?"})
  else:
    chat_model = chat_model.bind_tools(tools)
    response = chat_model.invoke([('user', 'What is 3 * 12?')])
    print(response.tool_calls)
  print(response)
