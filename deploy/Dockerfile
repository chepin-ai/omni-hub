# =============================================================================
# OMNI-HUB v12.0 — Docker Image
# =============================================================================
# Build:  docker build -f deploy/Dockerfile -t omni-hub:v12.0 .
# Run:    docker run -d --name omni-hub -p 7641:7641 omni-hub:v12.0
# =============================================================================

FROM python:3.11-slim-bookworm AS base

LABEL maintainer="OMNI-HUB Team <deploy@omni-hub.dev>"
LABEL version="12.0.0"
LABEL description="OMNI-HUB v12.0 — Unified Intelligence System"

# --- 系统依赖 ----------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# --- 创建用户 ----------------------------------------------------------------
RUN groupadd -r omni-hub && useradd -r -g omni-hub -d /opt/omni-hub -s /bin/bash omni-hub

# --- 工作目录 ----------------------------------------------------------------
WORKDIR /opt/omni-hub

# --- Python 依赖 --------------------------------------------------------------
COPY requirements.txt /opt/omni-hub/requirements.txt 2>/dev/null || echo "numpy>=1.24\nscipy>=1.10\nsympy>=1.12\nmatplotlib>=3.7\nnetworkx>=3.1\npsutil>=5.9\npyyaml>=6.0" > /opt/omni-hub/requirements.txt
RUN pip install --no-cache-dir -r /opt/omni-hub/requirements.txt

# --- 复制代码 ----------------------------------------------------------------
COPY core/ /opt/omni-hub/core/
COPY hub/ /opt/omni-hub/hub/
COPY formal/ /opt/omni-hub/formal/
COPY run_omni_hub.py /opt/omni-hub/run_omni_hub.py
COPY deploy/.env.template /opt/omni-hub/deploy/.env.template

# --- 目录权限 ----------------------------------------------------------------
RUN mkdir -p /var/log/omni-hub /var/lib/omni-hub && \
    chown -R omni-hub:omni-hub /opt/omni-hub /var/log/omni-hub /var/lib/omni-hub

# --- 健康检查 ----------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7641/health')" 2>/dev/null || exit 1

# --- 运行时 ------------------------------------------------------------------
USER omni-hub
ENV PYTHONPATH=/opt/omni-hub/core
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV OMNI_HUB_HOME=/opt/omni-hub
ENV OMNI_HUB_LOG_DIR=/var/log/omni-hub
ENV OMNI_HUB_STATE_DIR=/var/lib/omni-hub

EXPOSE 7641 9090

ENTRYPOINT ["python", "/opt/omni-hub/run_omni_hub.py"]
CMD ["--mode", "production"]
