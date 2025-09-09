#!/usr/bin/python3

huggingface_token = ''

tgi_host = "http://192.168.2.236:8104"

neo4j_host = "bolt://localhost:7687"
neo4j_user = "neo4j"
neo4j_password = "12345678"
neo4j_db = "neo4j"

use_fewshot = False
use_selector = False

node_types = ['Meeting', 'Time', 'Venue', 'Attendee', '', 'Patent Owner', 'Patent Citation']

rel_types = [
  ('Patent', 'Invented_by', 'Inventor'),
  ('Patent', 'Applied_by', 'Applicant'),
  ('Patent', 'Processed_by', 'Agent'),
  ('Patent', 'Belongs_to', 'Technical Field'),
  ('Patent', 'Owned_by', 'Patent Owner'),
  ('Patent', 'Cite', 'Patent')
]

examples = [
]
