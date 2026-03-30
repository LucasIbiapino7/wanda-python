FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["uvicorn", "wanda_python.app:app", "--host", "0.0.0.0", "--port", "8000"]