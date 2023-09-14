# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libffi-dev \
    libssl-dev

# Copy the requirements for the Python application
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main Python script
COPY main.py .

# Specify the port number the container should expose (if needed)
EXPOSE 8080

# Command to run the script
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
