# Introduction

this project is to generate reports with KG extracted from patents

# Usage

## Install prerequisites

```shell
sudo apt install docker.io docker-compose-v2
```

## Launch graphdb and vectordb service

```shell
cd docker
sudo mkdir /srv/shared
mkdir opensearch-data
sudo chown -R 1000:1000 ./opensearch-data
sudo chmod -R 770 ./opensearch-data
docker compose -f services.yaml up
```

## Create vectordb and graphdb

```shell
python3 create_vectordb_graphdb.py --env (qa|sit|uat|prod) --host <host/to/service> --port <port/of/service>
```

