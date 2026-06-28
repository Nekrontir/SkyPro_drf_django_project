# SkyPro DRF Django Project

Учебный Django REST Framework проект с PostgreSQL, Redis, Celery и Celery Beat, упакованный в Docker Compose.

Все части приложения (Django, база данных, Redis, Celery worker и Celery beat).



## Установка и настройка

1. Склонируйте репозиторий и перейдите в директорию проекта.

2. Создайте файл `.env` на основе примера:

   ```bash
   cp .env.example .env
   ```

3. При необходимости измените значения в `.env`:

    - `SECRET_KEY` — секретный ключ Django.
    - `PASSWORD` — пароль пользователя PostgreSQL.
    - Ключи Stripe, если они нужны.

Важно: для работы в Docker значения `HOST` и `REDIS_HOST` должны быть:

```env
HOST=db
REDIS_HOST=redis
```

## Сервисы

Docker Compose поднимает следующие сервисы:

- `web` — Django-приложение (API), доступно по адресу `http://localhost:8000`.
- `db` — PostgreSQL 16, база данных проекта.
- `redis` — Redis 7, брокер сообщений для Celery.
- `celery_worker` — Celery worker для обработки фоновых задач.
- `celery_beat` — Celery Beat для запуска периодических задач.

PostgreSQL и Redis доступны только внутри Docker-сети и не публикуются наружу (используется `expose`).

## Запуск приложения

Для полного запуска всех сервисов достаточно одной команды:

```bash
docker compose up --build
```

При запуске:

- Собираются Docker-образы.
- Запускаются контейнеры `db` и `redis`.
- Запускается контейнер `web`, в котором `entrypoint.sh`:
    - Дожидается готовности PostgreSQL (`pg_isready`).
    - Выполняет миграции базы данных: `python manage.py migrate --noinput`.
    - Выполняет сбор статики: `python manage.py collectstatic --noinput`.
    - Запускает сервер разработки: `python manage.py runserver 0.0.0.0:8000`.
- Запускаются `celery_worker` и `celery_beat`.

Дополнительные команды для миграций после запуска **не требуются** — приложение готово к работе сразу после `docker compose up --build`.

После успешного запуска:

- API доступен по адресу: `http://localhost:8000/`
- Документация API (если настроена в `urls.py` через drf-spectacular) — например, по адресу `/api/schema/` или `/api/docs/`.

## Управление контейнерами

Остановить все контейнеры:

```bash
docker compose down
```

Остановить и удалить контейнеры вместе с томами (данными PostgreSQL и Redis):

```bash
docker compose down -v
```

Перезапустить с пересборкой образов:

```bash
docker compose up --build
```

## Логи

Посмотреть логи Django-приложения:

```bash
docker compose logs -f web
```

Логи Celery worker:

```bash
docker compose logs -f celery_worker
```

Логи Celery Beat:

```bash
docker compose logs -f celery_beat
```

## Разработка

- Исходный код монтируется в контейнер `web` как volume (`.:/app`), поэтому изменения в коде видны без пересборки образа.
- Стиль кода и линтеры (Black, isort) настроены в `pyproject.toml`.
- Тесты можно запускать внутри контейнера:

  ```bash
  docker compose exec web coverage run manage.py test
  ```

## Структура для Docker

- `docker-compose.yml` — описание всех сервисов.
- `Dockerfile` — образ для Django, Celery worker и Celery Beat.
- `entrypoint.sh` — точка входа для сервиса `web` (ожидание базы, миграции, collectstatic, запуск сервера).
- `requirements.txt` — список Python-зависимостей.
- `.env` — переменные окружения (не хранится в репозитории).
- `.env.example` — пример конфигурации окружения.