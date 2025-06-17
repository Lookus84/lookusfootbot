FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Убедимся, что контейнер завершается при ошибках
ENV PYTHONUNBUFFERED=1
STOPSIGNAL SIGINT

CMD ["python", "bot.py"]
