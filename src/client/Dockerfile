# Use an official lightweight Python image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

USER root


# Install required tools
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    apt-transport-https \
    ca-certificates \
    software-properties-common

# Add Docker’s official GPG key
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker apt repository
RUN echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker CLI (not the daemon)
RUN apt-get update && apt-get install -y docker.io

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy client files into the container
COPY src/client.py .
COPY src/plot_cache_latency_plots.py .
COPY cache_latencies.sh .
COPY requirements.txt .
COPY src/plot_cache_evictions.py .
COPY replica_stop_and_restart_test.sh .
COPY simulate_crash_with_leader.sh .

# Only copy requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your app
COPY . .
RUN apt-get update && apt-get install -y jq
RUN apt-get install -y curl


# Ensure logs directory exists
RUN mkdir -p logs

# Default command (can be overridden in docker-compose)
CMD ["sh", "replica_stop_and_restart_test.sh"]

