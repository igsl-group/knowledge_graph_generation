#!/usr/bin/python3

from os import walk, mkdir
from os.path import splitext, join, exists, basename
from shutil import copyfile, rmtree
from uuid import uuid4
from absl import flags, app
from tqdm import tqdm
import json
import gradio as gr
from neo4j import GraphDatabase
from gradio_client import Client, handle_file
from langchain_text_splitters.markdown import MarkdownTextSplitter
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer, DiffbotGraphTransformer, RelikGraphTransformer, GlinerGraphTransformer
from models import *

FLAGS = flags.FLAGS

def add_options():
  flags.DEFINE_string('host', default = '0.0.0.0', help = 'service host')
  flags.DEFINE_integer('port', default = 8081, help = 'service port')
  flags.DEFINE_enum('api', default = 'vllm', enum_values = {'vllm', 'dashscope'}, help = 'which api to use')
  flags.DEFINE_enum('model', default = 'llm', enum_values = {'llm', 'diffbot', 'relik', 'gliner'}, help = 'model type')
  flags.DEFINE_enum('env', default = 'qa', enum_values = {'qa', 'sit', 'uat'}, help = 'environment to use')
  flags.DEFINE_string('shared_dir', default = '/srv/shared', help = 'shared folder')

def create_interface(configs):
  # 2) create graph llm
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
  # 3) make sure the graph database exists
  driver = GraphDatabase.driver(configs.neo4j_host, auth = (configs.neo4j_user, configs.neo4j_password))
  with driver.session() as session:
    db_exists = session.run("show databases").data()
    if not any(db['name'] == configs.neo4j_db for db in db_exists):
      session.run(f"create database {configs.neo4j_db}")
  driver.close()
  # 4) create graph database
  def create_graphdb(files, progress = gr.Progress()):
    neo4j = Neo4jGraph(url = configs.neo4j_host, username = configs.neo4j_user, password = configs.neo4j_password, database = configs.neo4j_db)
    client = Client("http://ocr-service:8081")
    splitter = MarkdownTextSplitter(chunk_size = 500, chunk_overlap = 50)
    shareddir = str(uuid4())
    mkdir(join(FLAGS.shared_dir, shareddir))
    results = list()
    for f in progress.tqdm(files):
      copyfile(f, join(FLAGS.shared_dir, shareddir, basename(f)))
      outputs = client.predict(files = [handle_file(join(FLAGS.shared_dir, shareddir, basename(f)))], api_name = "/do_ocr")
      results.append(outputs[0])
    docs = list()
    for result in results:
      markdown = result['markdown']
      docs.append(Document(page_content = markdown))
    splitted_docs = splitter.split_documents(docs)
    graph = graph_transformer.convert_to_graph_documents(splitted_docs)
    neo4j.add_graph_documents(graph)
    if exists(shareddir): rmtree(shareddir)
    return []
  with gr.Blocks() as demo:
    with gr.Column():
      with gr.Row(equal_height = True):
        files = gr.Files(label = "files to upload", scale = 3)
        process_btn = gr.Button('process', scale = 1)
      process_btn.click(create_graphdb, inputs = [files], outputs = [files], concurrency_limit = 64)
  return demo

def main(unused_argv):
  # 1) load configs
  if FLAGS.env == 'qa':
    import configs.qa_configs as configs
  elif FLAGS.env == 'sit':
    import configs.sit_configs as configs
  elif FLAGS.env == 'uat':
    import configs.uat_configs as configs
  else:
    raise Exception('unknown environment!')
  demo = create_interface(configs)
  demo.launch(server_name = FLAGS.host,
              server_port = FLAGS.port,
              share = False,
              show_error = True,
              max_threads = 64)

if __name__ == "__main__":
  add_options()
  app.run(main)
