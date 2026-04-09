FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY pyproject.toml README.md requirements.txt ./
COPY src ./src
COPY frontend ./frontend
COPY dashboard ./dashboard
COPY scripts ./scripts

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

EXPOSE 8010 8501
