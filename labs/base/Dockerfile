FROM python:3.11

LABEL maintainer="OPCP AI-Powered-Store Training Team"
LABEL description="Base container image for AI Store Labs exercise execution"

WORKDIR /lab

# Install system dependencies needed for exercises
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    jq \
    gosu \
    postgresql-client \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create directories for exercise workspace and results
RUN mkdir -p /lab/exercises /lab/results /lab/config

# Non-root user for exercise execution
RUN useradd -m -s /bin/bash learner \
    && chown -R learner:learner /lab

ENV PYTHONUNBUFFERED=1
ENV LAB_WORKSPACE=/lab
ENV LAB_RESULTS_DIR=/lab/results

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
