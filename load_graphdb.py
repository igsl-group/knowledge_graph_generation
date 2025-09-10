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
from opensearchpy import RequestsHttpConnection
from langchain_text_splitters.markdown import MarkdownTextSplitter
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
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
  def create_graphdb_from_files(files, progress = gr.Progress()):
    embedding = HuggingFaceEmbeddings(model_name = "Qwen/Qwen3-Embedding-0.6B")
    vectordb = OpenSearchVectorSearch(
      embedding_function = embedding,
      opensearch_url = configs.test_opensearch_host,
      index_name = configs.opensearch_text_semantic_index,
      engine = 'faiss',
      http_auth = (configs.test_opensearch_user, self.configs.test_opensearch_password),
      use_ssl = True,
      verify_certs = False,
      bulk_size = 100000000,
      connection_class = RequestsHttpConnection,
    )
    neo4j = Neo4jGraph(url = configs.neo4j_host, username = configs.neo4j_user, password = configs.neo4j_password, database = configs.neo4j_db)
    client = Client("http://ocr-service:8081")
    splitter = MarkdownTextSplitter(chunk_size = 800, chunk_overlap = 25)
    shareddir = str(uuid4())
    mkdir(join(FLAGS.shared_dir, shareddir))
    results = list()
    for f in progress.tqdm(files, desc = "ocr progress"):
      copyfile(f, join(FLAGS.shared_dir, shareddir, basename(f)))
      outputs = client.predict(files = [handle_file(join(FLAGS.shared_dir, shareddir, basename(f)))], api_name = "/do_ocr")
      results.extend(outputs)
    docs = [Document(page_content = result['markdown'], metadata = {"filename": basename(f)}) for result in results]
    splitted_docs = splitter.split_documents(docs)
    result_id_list = vectordb.add_documents(splitted_docs, timeout = "120s", vector_field = "vector_field", engine = "faiss", ef_construction = 512, ef_search = 512, m = 16)
    for opensearch_id, splitted_doc in progress.tqdm(zip(result_id_list, splitted_docs), desc = "triplets extraction progress"):
      splitted_doc.metadata['opensearch_id'] = opensearch_id
      graph = graph_transformer.convert_to_graph_documents([splitted_doc])
      neo4j.add_graph_documents(graph)
    if exists(shareddir): rmtree(shareddir)
    return []
  def create_graphdb_from_text(text, progress = gr.Progress()):
    vectordb = OpenSearchVectorSearch(
      embedding_function = embedding,
      opensearch_url = configs.test_opensearch_host,
      index_name = configs.opensearch_text_semantic_index,
      engine = 'faiss',
      http_auth = (configs.test_opensearch_user, self.configs.test_opensearch_password),
      use_ssl = True,
      verify_certs = False,
      bulk_size = 100000000,
      connection_class = RequestsHttpConnection,
    )
    neo4j = Neo4jGraph(url = configs.neo4j_host, username = configs.neo4j_user, password = configs.neo4j_password, database = configs.neo4j_db)
    doc = Document(page_content = text, metadata = {"filename": "text"})
    result_id_list = vectordb.add_documents([doc], timeout = "120s", vector_field = "vector_field", engine = "faiss", ef_construction = 512, ef_search = 512, m = 16)
    doc.metadata['opensearch_id'] = result_id_list[0]
    graph = graph_transformer.convert_to_graph_documents([doc])
    neo4j.add_graph_documents(graph)
    return ''
  with gr.Blocks() as demo:
    with gr.Tab("Production"):
      pass
    with gr.Tab("Test"):
      with gr.Column():
        with gr.Row(equal_height = True):
          files = gr.Files(label = "files to upload", scale = 3)
          ocr_triplets_btn = gr.Button('OCR+triplets extraction', scale = 1)
        ocr_triplets_btn.click(create_graphdb_from_files, inputs = [files], outputs = [files], concurrency_limit = 64)
        with gr.Row(equal_height = True):
          text = gr.Textbox(label = "text chunk", scale = 3)
          triplets_btn = gr.Button('triplets extraction', scale = 1)
        triplets_btn.click(create_graphdb_from_text, inputs = [text], outputs = [text], concurrency_limit = 64)
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
