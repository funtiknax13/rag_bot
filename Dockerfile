FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /app/docs /app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONPATH=/app/src

CMD ["python", "src/main.py"]
