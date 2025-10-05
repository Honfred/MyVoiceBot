FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot/ ./bot/
COPY setup.py .

# Install the bot package
RUN pip install -e .

# Create non-root user first
RUN useradd --create-home --shell /bin/bash botuser

# Create logs directory with proper permissions
RUN mkdir -p logs && \
    chown -R botuser:botuser /app

USER botuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import bot; print('healthy')" || exit 1

CMD ["python", "-m", "bot"]
