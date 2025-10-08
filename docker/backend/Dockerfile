FROM ghcr.io/astral-sh/uv:python3.11-bookworm

WORKDIR /app

# Ensure uv creates the project environment inside the container
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

# Install dependencies first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy the application source
COPY . .

# Re-run sync to install the project itself into the virtual environment
RUN uv sync --frozen --no-dev

COPY docker/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "python", "-m", "app.runner"]
