FROM dailyco/pipecat-base:latest-py3.11

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the backend code
COPY backend/ .
