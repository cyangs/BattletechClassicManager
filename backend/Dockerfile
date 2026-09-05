FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (separate layer so they're cached on code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Run migrations then start the API server.
# Shell form so the && chain works; uvicorn binds to 0.0.0.0 so Docker can
# forward the port from the host.
CMD alembic upgrade head && \
    uvicorn api:app --host 0.0.0.0 --port 8000
