FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH=/usr/local/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl jq tzdata \
    libffi-dev libssl-dev build-essential \
    libjpeg-dev zlib1g-dev libtiff-dev libopenjp2-7 libturbojpeg0 && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip wheel setuptools

RUN pip install --no-cache-dir homeassistant pre-commit ruff pytest pytest-asyncio

RUN mkdir -p /config \
 && chown -R vscode:vscode /config

WORKDIR /workspaces/app

EXPOSE 8123
