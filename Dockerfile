# Base image
FROM python:3.13-slim

# System deps for mysqlclient and build tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /code

# Python env tweaks
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies first (better layer caching)
COPY requirements.txt /code/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /code/

# Expose Django dev server port
EXPOSE 8002

# Default command (production-ready server)
CMD ["gunicorn", "backend_estadisticas.wsgi:application", "--bind", "0.0.0.0:8002"]
