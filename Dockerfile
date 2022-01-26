FROM python:3.8.12-buster

ARG pip_extra_index_url
ENV PIP_EXTRA_INDEX_URL $pip_extra_index_url

# add source code
ADD entrypoint.sh /usr/src/entrypoint.sh
ADD requirements.txt /usr/src/requirements.txt
ADD src /usr/src

# change working directory
WORKDIR /usr/src

# setup virtual environment
RUN python -m venv .venv && \
    . .venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Python module to be executed should be passed as the "command" to the container
ENTRYPOINT ["/usr/src/entrypoint.sh"]
