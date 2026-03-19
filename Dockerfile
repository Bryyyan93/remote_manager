# >= Python 3.12, base Debian para evitar líos con cryptography/paramiko
FROM python:3.12-slim-bookworm
USER root
# Ajustes básicos de runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Paquetes del sistema necesarios para paramiko/cryptography y ssh client
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates tzdata openssh-client \
    build-essential libffi-dev libssl-dev \
    python3-tk tk tcl \
 && rm -rf /var/lib/apt/lists/*

# Directorio de la app
WORKDIR /app

# Copiamos dependencias primero para cachear
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiamos el código
COPY api_onomondo ./api_onomondo
COPY app ./app
COPY ssh ./ssh

# Usuario no-root
RUN useradd -m appuser && chown -R appuser:appuser /app
# USER root

# Expone la API
EXPOSE 8000

# Healthcheck simple (requiere curl)
# RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
# HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
#   CMD curl -fsS http://127.0.0.1:8000/docs >/dev/null || exit 1

# Lanza FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
