# ===== Etapa 1: base python ligera
FROM python:3.11-slim AS base

# Evita bytecode y usa UTF-8
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala dependencias del sistema que a veces requiere numpy/pandas (muy livianas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# ===== Etapa 2: instala dependencias
FROM base AS deps
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ===== Etapa 3: runtime final
FROM base AS runtime
WORKDIR /app

# Copiamos las dependencias ya instaladas
COPY --from=deps /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=deps /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=deps /usr/local/bin/pip /usr/local/bin/pip

# Copia tu código y artefactos del modelo
COPY app.py .
COPY model.pth .
COPY scaler.pkl .

# Puerto
EXPOSE 8000

# Comando de arranque (1 worker con autoreload desactivado en prod)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
