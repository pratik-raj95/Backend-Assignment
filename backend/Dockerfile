# Stage 1: Build and Run
FROM python:3.11-slim

# Set system env variables to optimize Python performance inside Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

WORKDIR /app

# Install build dependencies and libgomp1 (required for FAISS CPU operations)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose FastAPI server port
EXPOSE 8000

# Startup script
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
