FROM python:3.10-slim

WORKDIR /app

COPY src/ ./src/
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

VOLUME ["/app/data"]

EXPOSE 6000

CMD ["python", "src/main.py"]
