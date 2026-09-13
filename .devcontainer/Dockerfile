FROM tensorflow/tensorflow:2.14.0-gpu

RUN apt update && apt install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    libxml2\
    libxslt1.1 \
    openssh-client \
    cmake \
    build-essential \
    libcublas-dev-11-8 \
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
    google-genai \
    playwright \
    nest_asyncio \
    tqdm \
    ddgs

ENV GGML_CUDA=1
ENV CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=50"
ENV FORCE_CMAKE=1

RUN pip install --no-cache-dir --no-binary llama-cpp-python llama-cpp-python

RUN playwright install && \
    playwright install-deps