# Imagen del recolector de histórico (scheduler.py).
# Solo empaqueta el collector y sus dependencias mínimas; la API y el
# frontend se ejecutan aparte.
FROM python:3.12-slim

WORKDIR /app

COPY requirements-collector.txt .
RUN pip install --no-cache-dir -r requirements-collector.txt

COPY app/ app/
COPY scheduler.py .

CMD ["python", "scheduler.py"]
