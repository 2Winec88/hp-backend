FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir \
    "celery>=5.6.3" \
    "daphne>=4.2.1" \
    "channels[daphne]>=4.3.2" \
    "channels-redis>=4.3.0" \
    "Django>=6.0.4" \
    "django-cors-headers>=4.9.0" \
    "django-debug-toolbar>=6.3.0" \
    "django-filter>=25.2" \
    "django-redis>=6.0.0" \
    "djangorestframework>=3.17.1" \
    "djangorestframework-simplejwt>=5.5.1" \
    "drf-spectacular>=0.29.0" \
    "pillow>=12.2.0" \
    "psycopg2-binary>=2.9.11" \
    "pyjwt>=2.12.1" \
    "python-decouple>=3.8" \
    "redis>=7.4.0" \
    "python-dotenv>=1.2.2" \
    "openpyxl>=3.1.5"

COPY . .

COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
