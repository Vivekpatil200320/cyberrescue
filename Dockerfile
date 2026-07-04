FROM python:3.12-slim

# Install modern high-speed uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency configurations
COPY pyproject.toml uv.lock* ./

# Install dependencies cleanly into the base system environment layer for the container
RUN uv sync --frozen --no-cache

# Copy project workspace modules
COPY . /app

# Ensure standard output buffering is disabled so JSON-RPC lines stream cleanly
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["uv", "run", "python", "-m", "cyberrescue.server"]
