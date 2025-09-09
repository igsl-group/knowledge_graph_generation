#!/usr/bin/python3

from os import walk, mkdir
from os.path import splitext, join, exists
from shutil import copyfile, rmtree
from uuid import uuid4
from absl import flags, app
from tqdm import tqdm
import json
from neo4j import GraphDatabase
from gradio_client import Client, handle_file
from langchain_text_splitters.markdown import MarkdownTextSplitter
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer, DiffbotGraphTransformer, RelikGraphTransformer, GlinerGraphTransformer
from models import *

FLAGS = flags.FLAGS

def add_options():
  flags.DEFINE_string('input_dir', default = None, help = 'path to directory')
  flags.DEFINE_enum('api', default = 'vllm', enum_values = {'vllm', 'dashscope'}, help = 'which api to use')
  flags.DEFINE_enum('model', default = 'llm', enum_values = {'llm', 'diffbot', 'relik', 'gliner'}, help = 'model type')
  flags.DEFINE_enum('env', default = 'qa', enum_values = {'qa', 'sit', 'uat'}, help = 'environment to use')
  flags.DEFINE_string('shared_dir', default = '/srv/shared', help = 'shared folder')

def main(unused_argv):
  if FLAGS.env == 'qa':
    import configs.qa_configs as configs
  elif FLAGS.env == 'sit':
    import configs.sit_configs as configs
  elif FLAGS.env == 'uat':
    import configs.uat_configs as configs
  else:
    raise Exception('unknown environment!')
  if FLAGS.model == 'llm':
    if FLAGS.api == 'vllm':
      llm = Qwen3_vllm(configs)
    elif FLAGS.api == 'dashscope':
      llm = Tongyi(configs)
    else:
      raise Exception('unknown api!')
    graph_transformer = LLMGraphTransformer(llm = llm, ignore_tool_usage = True)
  elif FLAGS.model == 'diffbot':
    graph_transformer = DiffbotGraphTransformer(diffbot_api_key = diffbot_api_key)
  elif FLAGS.model == 'relik':
    graph_transformer = RelikGraphTransformer()
  elif FLAGS.model == 'gliner':
    graph_transformer = GlinerGraphTransformer()
  else:
    raise Exception('unknown graph transformer type!')
  driver = GraphDatabase.driver(neo4j_host, auth = (neo4j_user, neo4j_password))
  with driver.session() as session:
    db_exists = session.run("show databases").data()
    if not any(db['name'] == neo4j_db for db in db_exists):
      session.run(f"create database {neo4j_db}")
  driver.close()
  neo4j = Neo4jGraph(url = neo4j_host, username = neo4j_user, password = neo4j_password, database = neo4j_db)
  client = Client("http://ocr-service:8081")
  splitter = MarkdownTextSplitter(chunk_size = 500, chunk_overlap = 50)
  shareddir = str(uuid4())
  mkdir(join(FLAGS.shared_dir, shareddir))
  for root, dirs, files in tqdm(walk(FLAGS.input_dir)):
    for f in files:
      stem, ext = splitext(f)
      if ext.lower() == '.pdf':
        copyfile(join(root, f), join(FLAGS.shared_dir, shareddir, f))
        results = client.predict(files = [handle_file(join(FLAGS.shared_dir, shareddir, f))], api_name = "/do_ocr")
        markdown = results[0]['markdown']
        docs = [Document(page_content = markdown)]
      else:
        continue
      docs = splitter.split_documents(docs)
      graph = graph_transformer.convert_to_graph_documents(docs)
      print(graph)
      neo4j.add_graph_documents(graph)
  if exists(shareddir): rmtree(shareddir)

if __name__ == "__main__":
  add_options()
  app.run(main)
