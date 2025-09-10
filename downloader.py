#!/usr/bin/python3

from abc import ABC, abstractmethod
import boto3
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse

class BaseDownloader(ABC):
  @abstractmethod
  def download(self, url, filename):
    pass

class AWSDownloader(BaseDownloader):
  def __init__(self, configs):
    self.client = boto3.client('s3',
                               aws_access_key_id = configs.aws_access_key_id,
                               aws_secret_access_key = configs.aws_secret_access_key,
                               endpoint_url = configs.endpoint_url if hasattr(configs, 'endpoint_url') else None,
                               region_name = "ap-east-1",
                               verify = False)
    self.configs = configs
  def download(self, url, filename):
    parsed_url = urlparse(url)
    obj = parsed_url.path
    if obj.startswith('/'): obj = obj[1:]
    self.client.download_file(self.configs.bucket_name, obj, filename)
    return filename

class Alfresco(BaseDownloader):
  def __init__(self, configs = None):
    pass
  def download(self, url, filename):
    response = requests.get(url, auth = HTTPBasicAuth('admin','admin'), verify = False)
    assert response.status_code == 200
    with open(filename, 'wb') as f:
      f.write(response.content)
    return filename

if __name__ == "__main__":
  downloader = AWSDownloader()
  downloader.download('https://terraform-ha-kms-bucket.s3.ap-east-1.amazonaws.com/Web/1011_index.html', 'test.html')
  '''
  import json
  with open('test.md', 'r') as f:
    data = json.loads(f.read())
  for key, value in data.items():
    with open(f'/mnt/c/Users/IGS/Downloads/{key}.md', 'w') as f:
      f.write(value)
  '''
