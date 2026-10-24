FROM python:3.11-slim

# HF Spaces requiere usuario no-root
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-descargar modelos durante el build para arranque rápido.
# U2NET_HOME fijo: el build corre como root pero el server como `user`;
# sin esto el modelo queda en /root/.u2net y se re-descarga al arrancar.
ENV U2NET_HOME=/home/user/.u2net
RUN python -c "\
from rembg import new_session; \
print('Descargando birefnet-general...'); \
new_session('birefnet-general'); \
print('Modelos listos')" && chown -R user:user /home/user/.u2net

COPY --chown=user main.py .

USER user
EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
