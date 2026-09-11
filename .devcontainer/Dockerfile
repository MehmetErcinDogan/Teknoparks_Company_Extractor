FROM tensorflow/tensorflow:2.14.0-gpu

RUN apt update && apt install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    libxml2\
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    ipykernel \
    requests \
    curl_cffi \
    beautifulsoup4 \
    lxml \
    pandas \
    python-dotenv \
    openai \
    google-genai

RUN pip install --no-cache-dir \
    llama-cpp-python \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu118