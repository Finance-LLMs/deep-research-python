FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY src/ src/
COPY .env.local .env.local

# Expose port
EXPOSE 3051

# Run the API server
CMD ["python", "-m", "src.api"]
