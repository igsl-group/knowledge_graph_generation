#!/usr/bin/python3

from os import walk
from os.path import splitext, join, exists
from absl import flags, app
from tqdm import tqdm
import json
from transformers import AutoTokenizer
from langchain.document_loaders import UnstructuredPDFLoader, UnstructuredHTMLLoader, TextLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer, RelikGraphTransformer
from configs import neo4j_host, neo4j_user, neo4j_password, neo4j_db, node_types, rel_types
from prompts import extract_triplets_template
from models import Qwen2_5

FLAGS = flags.FLAGS

def add_options():
  flags.DEFINE_string('input_dir', default = None, help = 'path to directory')
  flags.DEFINE_boolean('split', default = False, help = 'whether to split document')

def main(unused_argv):
  prompt = extract_triplets_template(node_types, rel_types)
  llm = Qwen2_5()
  '''
  graph_transformer = LLMGraphTransformer(
    llm = llm,
    prompt = prompt,
    #allowed_nodes = node_types,
    #allowed_relationships = rel_types,
  )
  '''
  graph_transformers = RelikGraphTransformer()
  neo4j = Neo4jGraph(url = neo4j_host, username = neo4j_user, password = neo4j_password, database = neo4j_db)
  if FLAGS.split:
    text_splitter = RecursiveCharacterTextSplitter(separators = [r"\n\n", r"\n", r"\.(?![0-9])|(?<![0-9])\.", r"。"], is_separator_regex = True, chunk_size = 150, chunk_overlap = 10)
  for root, dirs, files in tqdm(walk(FLAGS.input_dir)):
    for f in files:
      stem, ext = splitext(f)
      if ext.lower() in ['.htm', '.html']:
        loader = UnstructuredHTMLLoader(join(root, f))
      elif ext.lower() == '.txt':
        loader = TextLoader(join(root, f))
      elif ext.lower() == '.pdf':
        loader = UnstructuredPDFLoader(join(root, f), mode = 'single')
      elif ext.lower() == '.md':
        loader = UnstructuredMarkdownLoader(join(root, f))
      else:
        raise Exception('unknown format!')
      docs = loader.load()
      if FLAGS.split:
        docs = text_splitter.split_documents(docs)
      graph = graph_transformer.convert_to_graph_documents(docs)
      neo4j.add_graph_documents(graph)

if __name__ == "__main__":
  add_options()
  app.run(main)
