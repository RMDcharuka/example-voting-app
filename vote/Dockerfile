# ----------------------
# Base stage
# ----------------------
    FROM python:3.11-slim AS base

    # Add curl for healthcheck
    RUN apt-get update && \
        apt-get install -y --no-install-recommends curl && \
        rm -rf /var/lib/apt/lists/*
    
    # Set the working directory
    WORKDIR /usr/local/app
    
    # Copy and install dependencies
    COPY requirements.txt ./requirements.txt
    RUN pip install --no-cache-dir -r requirements.txt
    
    # ----------------------
    # Development stage
    # ----------------------
    FROM base AS dev
    
    # Copy all source code and tests into the container
    COPY . .
    
    # Install development/test dependencies
    RUN pip install watchdog pytest
    
    # Set Flask environment for development
    ENV FLASK_ENV=development
    
    # Command to run development server
    CMD ["python", "app.py"]
    
    # ----------------------
    # Production stage
    # ----------------------
    FROM base AS final
    
    # Copy only source code for production
    COPY . .
    
    # Expose port
    EXPOSE 80
    
    # Command to run Gunicorn for production
    CMD ["gunicorn", "app:app", "-b", "0.0.0.0:80", "--log-file", "-", "--access-logfile", "-", "--workers", "4", "--keep-alive", "0"]
    