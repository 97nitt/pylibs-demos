# pylibs demos

This repository contains Python applications that demonstrate some of the features in [pylibs](https://github.com/97nitt/pylibs).

## Applications

The demo applications can be run using [Docker Compose](https://docs.docker.com/compose/).

Configuration of the applications is done using environment variables. You can configure the apps by adding a `.env` 
file in the root directory of this project. The variables used by each app can be found in [docker-compose.yaml](docker-compose.yaml).

| Command                              | Description                                          |
|--------------------------------------|------------------------------------------------------|
| `docker compose up kafka-clients`    | Starts a Kafka producer and consumer                 |
| `docker compose up kinesis-consumer` | Starts a multi-threaded consumer of a Kinesis stream |

## Local Development

Create a **Python 3.8** virtual environment:
```
python -m venv --prompt pylibs .venv
source .venv/bin/activate
```

Install project dependencies:
```
pip install -r requirements.txt
```
