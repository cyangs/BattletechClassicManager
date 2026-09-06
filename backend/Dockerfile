FROM python:3.12-slim

WORKDIR /app

# Install PostgreSQL 17 client tools (pg_dump) for the database-backup feature.
# The version must match the server (postgres:17-alpine), so we pull from the
# official PostgreSQL apt repository (PGDG) rather than Debian's older default.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg lsb-release \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
        -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-17 \
    && apt-get purge -y curl gnupg lsb-release \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

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
