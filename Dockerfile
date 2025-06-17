FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TELEGRAM_TOKEN=${TELEGRAM_TOKEN} \
    PORT=8080

CMD ["python", "bot.py"]
