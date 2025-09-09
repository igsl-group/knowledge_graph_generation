#!/usr/bin/python3

from os import walk
from os.path import splitext, join, exists
from absl import flags, app
from tqdm import tqdm
import json
from neo4j import GraphDatabase
from transformers import AutoTokenizer
from langchain.document_loaders import UnstructuredPDFLoader, UnstructuredHTMLLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer, DiffbotGraphTransformer, RelikGraphTransformer, GlinerGraphTransformer
from configs import *
from models import *

FLAGS = flags.FLAGS

def add_options():
  flags.DEFINE_string('input_dir', default = None, help = 'path to directory')
  flags.DEFINE_boolean('split', default = False, help = 'whether to split document')
  flags.DEFINE_enum('api', default = 'tgi', enum_values = {'tgi', 'dashscope'}, help = 'which api to use')
  flags.DEFINE_enum('model', default = 'llm', enum_values = {'llm', 'diffbot', 'relik', 'gliner'}, help = 'model type')

def main(unused_argv):
  if FLAGS.model == 'llm':
    if FLAGS.api == 'tgi':
      llm = Qwen2_5()
    elif FLAGS.api == 'dashscope':
      llm = Tongyi()
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
  if FLAGS.split:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 50)
  for root, dirs, files in tqdm(walk(FLAGS.input_dir)):
    for f in files:
      stem, ext = splitext(f)
      if ext.lower() in ['.htm', '.html']:
        loader = UnstructuredHTMLLoader(join(root, f))
      elif ext.lower() == '.txt':
        loader = TextLoader(join(root, f))
      elif ext.lower() == '.pdf':
        loader = UnstructuredPDFLoader(join(root, f), mode = 'single', strategy = "hi_res", languages = ['eng', 'chi_sim', 'chi_tra'])
      else:
        raise Exception('unknown format!')
      docs = loader.load()
      if FLAGS.split:
        docs = text_splitter.split_documents(docs)
      graph = graph_transformer.convert_to_graph_documents(docs)
      print(graph)
      neo4j.add_graph_documents(graph)

if __name__ == "__main__":
  add_options()
  app.run(main)
