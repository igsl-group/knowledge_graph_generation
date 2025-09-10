#!/usr/bin/python3

MAX_CONCURRENT_REQUESTS=32

langsmith_trace = 'false'
langsmith_api_key = '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'

service_host = "0.0.0.0"
service_port = 8081
opensearch_host = [
  {'host': '172.29.2.138', 'port': 9200},
  {'host': '172.29.2.139', 'port': 9200},
  {'host': '172.16.103.107', 'port': 9200}
]
opensearch_user = "admin"
opensearch_password = "admin"

test_opensearch_host = [
  {"host": "opensearch", 'port': 9200}
]   
test_opensearch_user = "admin"
test_opensearch_password = "G2w$8nRf!qTbZ7kA"

endpoint_url = 'https://uat.eoss.housingauthority.gov.hk:9021'
aws_access_key_id = 'akms01'
aws_secret_access_key = 'UdrQWl/ILp5+/ftu6ohCjhm0G4sDJQ4vomGHog+c'
bucket_name = 'akmsbk01'

opensearch_fulltext_index = "uat_text_index"
opensearch_text_semantic_index = "uat_text_semantic_index"
opensearch_drawing_semantic_index = "uat_drawing_semantic_index"
opensearch_faq_index = "faq"
opensearch_drawing_keyword_index = "uat_drawing_index"
thinking = False

psql_host = "172.16.103.137"
psql_port = "5000"
psql_user = "kmsuser"
psql_db = "kms"
psql_password = "KMS@2025!"

tgi_host = "http://172.29.2.138:8080"
vllm_host = "http://172.29.2.138:8000/v1"
dashscope_api = "https://dashscope.aliyuncs.com/compatible-mode/v1"
dashscope_api_key = 'sk-88f509096c9f45c79f16cad6adbba753'
huggingface_api_key = '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'
thinking = False

neo4j_host = "bolt://neo4j:7687"
neo4j_user = "neo4j"
neo4j_password = "12345678"
neo4j_db = "neo4j"

child_chunk_size = 500
child_overlap_size = 50
parent_chunk_size = 2000
parent_overlap_size = 200

