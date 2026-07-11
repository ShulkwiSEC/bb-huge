FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system deps — gcc for pip C-extension builds; the rest
# (git/curl/ca-certificates/unzip/build-essential/libpcap-dev) are
# prerequisites for assets/scripts/bb-install-tools.sh, which the
# user runs on demand to install the recon toolkit (subfinder, httpx, etc.)
# used by app/recon_runner.py — not installed at image-build time by
# default, to keep the base image build fast.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc git curl ca-certificates unzip build-essential libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create required directories
RUN mkdir -p instance app/static/uploads

# Don't run as root
# Pre-create the Go install dirs (as bbhuge, before they become volume mount
# points in docker-compose.yml) so bb-install-tools.sh never needs root.
RUN useradd -m -u 1000 bbhuge && \
    mkdir -p /home/bbhuge/.local /home/bbhuge/go && \
    chown -R bbhuge:bbhuge /app /home/bbhuge
USER bbhuge

# Go toolchain + installed recon tools live here once
# bb-install-tools.sh has been run (see docker-compose.yml volumes) — both
# installed entirely under the bbhuge user's home so the script never needs
# root/sudo. On PATH unconditionally so app/recon_runner.py's subprocess
# calls find them without needing a login shell / .bashrc sourced.
ENV GOPATH=/home/bbhuge/go
ENV PATH="/home/bbhuge/.local/go/bin:/home/bbhuge/go/bin:${PATH}"

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "run.py"]
