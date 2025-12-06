FROM dailyco/pipecat-base:latest-py3.11

WORKDIR /app

# Copy requirements and install dependencies with cache mount
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy the backend code
COPY backend/ ./
