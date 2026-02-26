# FROM python:3.11-slim

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# WORKDIR /app

# RUN apt-get update \
#     && apt-get install -y --no-install-recommends build-essential libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# COPY backend/requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir -r /app/requirements.txt

# COPY backend /app

# RUN mkdir -p /app/media /app/staticfiles

# CMD ["/bin/sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"]


FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app

RUN mkdir -p /app/media /app/staticfiles

CMD ["/bin/sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"]
