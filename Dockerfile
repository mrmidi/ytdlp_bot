# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml README.md ./

# Install project dependencies
RUN uv pip install --system .

# Copy application source code
COPY src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "-m", "src.main"]
