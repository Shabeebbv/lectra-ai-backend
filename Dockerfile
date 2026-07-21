FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip \
    # CPU-only torch first -- avoids pulling the ~3-6GB NVIDIA/CUDA stack,
    # which is useless on this EC2 instance since it has no GPU.
    && pip install --no-cache-dir torch==2.12.1 --index-url https://download.pytorch.org/whl/cpu \
    # Then everything else. pip sees torch==2.12.1 already satisfied
    # (exact version match) and will not re-fetch the GPU build.
    && pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]