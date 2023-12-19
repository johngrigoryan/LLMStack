FROM python:3.10

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    x11vnc \
    novnc \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install poetry

# Disable virtualenv creation
RUN poetry config virtualenvs.create false

# Empty dir for web
RUN mkdir -p /usr/share/www/html

# Set up working directory
RUN mkdir /code
WORKDIR /code

# Copy project files
COPY poetry.lock /code/poetry.lock
COPY pyproject.toml /code/pyproject.toml
COPY README.md /code/README.md
COPY llmstack /code/llmstack
COPY runner/docker-entrypoint.sh /code/docker-entrypoint.sh
COPY .llmstack /root/.llmstack
# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Set up entry point and expose port
RUN chmod +x /code/docker-entrypoint.sh
EXPOSE 3000
ENTRYPOINT [ "/code/docker-entrypoint.sh" ]
CMD ["llmstack"]


