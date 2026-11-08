# Curizx MCP Server Dockerfile
# Brand: Curizx AI by Rayhan
# Intelligent Tools for AI-Powered Development

FROM python:3.11-slim

# Avoid writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies if needed (e.g. git for VCS operations)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose MCP server port
EXPOSE 8000

# Execute Curizx MCP Server
CMD ["python", "server.py"]
