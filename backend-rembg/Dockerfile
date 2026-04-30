FROM python:3.11-slim

# HF Spaces requiere usuario no-root
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-descargar modelos durante el build para arranque rápido
RUN python -c "\
from rembg import new_session; \
print('Descargando u2net_cloth_seg...'); \
new_session('u2net_cloth_seg'); \
print('Descargando birefnet-general...'); \
new_session('birefnet-general'); \
print('Modelos listos')"

COPY --chown=user main.py .

USER user
EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
