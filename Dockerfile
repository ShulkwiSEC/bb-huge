FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create required directories
RUN mkdir -p instance app/static/uploads

# Don't run as root
RUN useradd -m -u 1000 bbhuge && \
    chown -R bbhuge:bbhuge /app
USER bbhuge

EXPOSE 5000

CMD ["python", "run.py"]
