
# Use the Python slim image
FROM python:3.13-slim

# Set the working directory
WORKDIR /locust

# Copy requirements
COPY requirements.txt .

# Install necessary build tools
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get install -y gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install -r requirements.txt

# Copy the locustfile.py
COPY locustfile.py .

# Expose Locust ports
EXPOSE 8089 5557

ENTRYPOINT ["locust"]

# Set the command to run Locust
CMD ["locust", "-f", "locustfile.py"]
