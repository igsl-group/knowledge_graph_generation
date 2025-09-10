#!/usr/bin/python3

from absl import flags, app
from os import remove
from os.path import exists
import re
import json
from datetime import datetime
from uuid import uuid4
from shutil import copyfile
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.automap import automap_base
from gradio_client import Client, handle_file
import opencc
from downloader import AWSDownloader, Alfresco

FLAGS = flags.FLAGS

def add_options():
  flags.DEFINE_string('host', default = 'localhost', help = 'server host')
  flags.DEFINE_integer('port', default = 8081, help = 'server port')
  flags.DEFINE_enum('env', default = 'qa', enum_values = {'qa', 'sit', 'uat', 'prod'}, help = 'which environment to use')

def main(unused_argv):
  if FLAGS.env == 'qa':
    import configs.qa_configs as configs
  elif FLAGS.env == 'sit':
    import configs.sit_configs as configs
  elif FLAGS.env == 'uat':
    import configs.uat_configs as configs
  elif FLAGS.env == 'prod':
    import configs.prod_configs as configs
  else:
    raise Exception('invalid environment!')
  converter = opencc.OpenCC('s2t')
  engine = create_engine(f"postgresql+psycopg2://{configs.psql_user}:password@{configs.psql_host}:{configs.psql_port}/{configs.psql_db}?password={configs.psql_password}", pool_pre_ping = True, pool_recycle = 3600)
  metadata = MetaData()
  metadata.reflect(bind = engine)
  Base = automap_base(metadata = metadata)
  Base.prepare()
  Session = sessionmaker(bind = engine)
  session = Session()
  KmsNodeVer = Base.classes.KMS_NODE_VER
  sql = f"""select "VER_ID", "NODE_ID", "VER_NUM", "OPENSEARCH_ID", "CATG_ID", "NAME", "TITLE", "LANG", "SOURCE_PATH", "NODE_PATH", "NODE_DATE", "OCR_PATH", "IS_DEL", "CURR_VER", "KMS_NODE_VER"."CRE_AT" as "CRE_AT", "KMS_NODE_VER"."DATE_LAST_MDF" as "DATE_LAST_MDF" from "KMS_NODE_VER", "KMS_NODE" where "NODE_ID" = "KMS_NODE_ID" and "TYPE" = '{type_name}' and "OCR_DONE" = true and "IS_DEL" = false"""
  results = pd.read_sql_query(sql, engine)
  for idx, row in results.iterrows():
    if '/STR/DOC/Calculation/' in row['SOURCE_PATH']: continue
    # 0) get category and groups
    if row['CATG_ID'] is not None:
      category = [row['CATG_ID']]
    else:
      category = []
    groups = pd.read_sql_query("""select "USER_GRP_ID" from "KMS_NODE_USER_GRP" where "KMS_NODE_ID" = %d;""" % row['NODE_ID'], engine)
    if len(groups) == 0:
      groups = []
    else:
      groups = [r['USER_GRP_ID'] for idx, r in groups.iterrows()]
    # 1) get revision date time
    creation_datetime = row['CRE_AT']
    revision_datetime = row['DATE_LAST_MDF']
    # 2) download documents objects
    tmpfile = str(uuid4())
    try:
      if FLAGS.env in {'sit', 'uat'}:
        if row['OCR_PATH'].startswith('s3'):
          AWSDownloader(configs).download(row['OCR_PATH'], tmpfile)
        elif 'alfresco'in row['OCR_PATH']:
          Alfresco(configs).download(row['OCR_PATH'], tmpfile)
        else:
          copyfile(row['OCR_PATH'], tmpfile)
      else:
        downloader = AWSDownloader(configs)
        downloader.download(row['OCR_PATH'], tmpfile)
    except:
      if exists(tmpfile): remove(tmpfile)
      print(f"""file at ocr_path of {row['OCR_PATH']} is invalid! skipped this file!""")
      continue
    # 3) get ocr results as markdown
    with open(tmpfile, 'r') as f:
      jsondata = json.loads(f.read())
    if len(jsondata) == 0:
      print(f"{row['NODE_ID']}: {row['NAME']} has no output from OCR!")
      if exists(tmpfile): remove(tmpfile)
      continue
    markdown = '\n'.join([content for page_num, content in jsondata.items()])
    if exists(tmpfile): remove(tmpfile)
    markdown = re.sub(r'\t|\n| {2,}', "", markdown)
    markdown = re.sub(r'!\[.*\]\(.*\)', '', markdown)
    markdown = re.sub(r'<img[^>]*>', '', markdown)
    markdown = converter.convert(markdown)
    # 4) get metadata
    metadata = {
      'filename': row['NAME'],
      'title': row['TITLE'],
      'lang': row['LANG'],
      'page_num': 1,
      'url': row['SOURCE_PATH'],
      'file_path': row['NODE_PATH'],
      'timestamp': row['NODE_DATE'] if not pd.isna(row['NODE_DATE']) else None,
      'doc_id': row['OPENSEARCH_ID'],
      'version': row['VER_NUM'],
      'category': category, 
      'groups': groups, 
      'last_modified': revision_datetime.strftime('%Y-%m-%d'),
      'created_at': creation_datetime.strftime('%Y-%m-%d'),
      'is_delete': row['IS_DEL'],
      'is_latest': row['VER_NUM'] == row['CURR_VER']
    }
    # 5) write to vectordb and graphdb
    try:
      client = Client('http://{FLAGS.host}:{FLAGS.port}')
      result = client.predict(
        markdown = markdown,
        metadata = metadata,
        api_name = "/add_vectordb_graphdb"
      )
    except:
      print(f"{row['NAME']} failed to add to vectordb and graphdb!")
      continue
    # 6) update db
    session.query(KmsNodeVer).filter(KmsNodeVer.VER_ID == row['VER_ID']).update(
      {
        "VECTORDB_DONE": True,
        "VECTORDB_DT": datetime.now(),
        "VECTOR_BY": "kmsuser"
      }
    )
    session.commit()

if __name__ == "__main__":
  add_options()
  app.run(main)    
