FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_CREATE=false

# Install build dependencies
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Generate lock file to suppress mismatch errors
RUN poetry lock --no-update

# Install project dependencies non-interactively
RUN poetry install --no-root

COPY . .

# Generate Protobuf bindings statically inside the container
RUN python -m grpc_tools.protoc -I. --python_out=. schema/market_data.proto

CMD ["python", "-m", "src.api"]
