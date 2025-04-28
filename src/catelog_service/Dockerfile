FROM python:3.10-slim

WORKDIR /app

COPY src/ ./src/
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# This is the path inside container where volume will be mounted
VOLUME ["/app/data"]

EXPOSE 5002

CMD ["python", "src/main.py"]
