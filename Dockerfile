# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Expose port (default 8000, can be overridden by PORT env var)
EXPOSE 8000

# Command to run the application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
