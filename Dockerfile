# Use a lightweight Python base image
FROM python:3.12-slim

# Copy the modern 'uv' binary into our container for hyper-fast dependency isolation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set a clean working directory inside the container space
WORKDIR /app

# Copy your configuration files first to optimize Docker layer caching
COPY pyproject.toml uv.lock* ./

# Install project dependencies atomically without creating virtualenvs manually
RUN uv sync --frozen --no-cache

# Copy the rest of your server code into the container environment
COPY . /app

# Explicitly use standard I/O for MCP communication (Glama reads stdin/stdout)
ENTRYPOINT ["uv", "run", "python", "-m", "cyberrescue.server"]
