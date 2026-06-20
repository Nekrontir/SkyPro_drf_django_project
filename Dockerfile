FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# Сначала копируем только requirements.txt — это кэшируется
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Теперь копируем весь проект
COPY . .

# entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# collectstatic можно делать при запуске, а не при сборке,
# чтобы не упираться в отсутствие env/базы на этапе build