# Use official Python 3.12-slim base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501

# Set working directory
WORKDIR /app

# Install system dependencies needed for compiling extensions if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
# Convert UTF-16 to UTF-8 if needed, then pip install
RUN iconv -f UTF-16 -t UTF-8 requirements.txt > requirements_utf8.txt && \
    pip install --no-cache-dir -r requirements_utf8.txt && \
    pip install --no-cache-dir fastapi uvicorn reportlab

# Copy the rest of the application
COPY . .

# Expose ports for Streamlit and FastAPI
EXPOSE 8501
EXPOSE 8000

# Default entry point is to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
