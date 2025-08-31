FROM python:3.10-slim-bullseye

WORKDIR /app

# Install system dependencies for web3 (minimal set)
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code
COPY . .

# Expose the MCP server port
EXPOSE 3000

# Start the MCP server
CMD ["python", "server.py"]
