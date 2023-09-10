# Dockerfile

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:80", "--workers", "4"]
