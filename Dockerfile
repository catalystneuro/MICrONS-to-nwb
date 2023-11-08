FROM python:3.8

RUN apt-get update --yes && \
    apt-get upgrade --yes && \
    apt-get install --yes --no-install-recommends

RUN python3 -m pip install --no-cache-dir --upgrade jupyterlab

WORKDIR /root
ARG CLOUDVOLUME_TOKEN
RUN mkdir -p .cloudvolume/secrets
RUN echo "{\"token\": \"${CLOUDVOLUME_TOKEN:-}\"}" > .cloudvolume/secrets/cave-secret.json

COPY . /src/microns-to-nwb
RUN pip install -e /src/microns-to-nwb


