FROM python:3.10-slim-bullseye

# Define some environment variables
ENV PIP_NO_CACHE_DIR=true \
    DEBIAN_FRONTEND=noninteractive

# Install dependencies needed to download/install packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    apt-utils \
    curl

# Upgrade system-wide pip/setuptools
RUN pip install --upgrade pip setuptools

# Install poetry
ENV PATH="$PATH:/root/.local/bin"
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python - --version 1.1.13
RUN poetry config virtualenvs.create false

# Install runtime dependencies (will be cached)
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-root

# Copy project files to container
COPY src ./src

# Install our own package
RUN poetry install --no-dev

# Run this command
CMD ["uvicorn",  "trafikkmeldinger.app:app", "--host", "0.0.0.0", "--port", "80"]
