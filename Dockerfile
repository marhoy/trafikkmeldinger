FROM python:3.10-slim-bullseye

# Define some environment variables
ENV PIP_NO_CACHE_DIR=true \
    DEBIAN_FRONTEND=noninteractive

# Install dependencies needed to download/install packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    apt-utils \
    curl

# We want to run things as a non-privileged user
ENV USERNAME=api
ENV PATH="$PATH:/home/$USERNAME/.local/bin"

# Add user and set up a workdir
RUN useradd -m $USERNAME
WORKDIR /home/$USERNAME/app
RUN chown $USERNAME.$USERNAME .

# Everything below here runs as a non-privileged user
USER $USERNAME

# Install poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python - --version 1.1.13
# RUN poetry config virtualenvs.create false

# Install runtime dependencies (will be cached)
COPY --chown=$USERNAME:$USERNAME pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-root

# Copy project files to container
COPY --chown=$USERNAME:$USERNAME src ./src

# Install our own package
RUN poetry install --no-dev

# Run this command
EXPOSE 5000
ENTRYPOINT ["poetry", "run"]
CMD ["uvicorn",  "trafikkmeldinger.api:app", "--host", "0.0.0.0", "--port", "5000"]
