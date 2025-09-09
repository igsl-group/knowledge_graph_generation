#!/usr/bin/python3

MAX_CONCURRENT_REQUESTS=32

langsmith_trace = 'true'
langsmith_api_key = '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'

service_host = "0.0.0.0"
service_port = 8081
opensearch_host = [
  {'host': '192.168.80.31', 'port': 9200},
  {'host': '192.168.80.32', 'port': 9200},
  {'host': '192.168.80.40', 'port': 9200}
]
opensearch_user = "admin"
opensearch_password = "admin"

opensearch_fulltext_index = "dev_text_index"
opensearch_text_semantic_index = "dev_text_semantic_index"
opensearch_drawing_semantic_index = "dev_drawing_semantic_index"
opensearch_faq_index = "faq"
opensearch_drawing_keyword_index = "dev_drawing_index"

psql_host = '192.168.80.45'
psql_port = '5432'
psql_user = "dbuser"
psql_db = 'housing_backend'
psql_password = "P@ssw0rd"

tgi_host = "http://192.168.80.21:8080"
vllm_host = "http://192.168.3.220:8000/v1"
dashscope_api = "https://dashscope.aliyuncs.com/compatible-mode/v1"
dashscope_api_key = 'sk-88f509096c9f45c79f16cad6adbba753'
huggingface_api_key = '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'

neo4j_host = "bolt://neo4j:7687"
neo4j_user = "neo4j"
neo4j_password = "12345678"
neo4j_db = "neo4j"

child_chunk_size = 500
child_overlap_size = 50
parent_chunk_size = 2000
parent_overlap_size = 200

