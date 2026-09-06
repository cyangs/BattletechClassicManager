# BattleTech Classic Manager

A campaign/session manager for BattleTech Classic — a mech & weapon library plus
game sessions with turn-based weapon-fire resolution (to-hit rolls, hit
locations, per-session weapon state, and an event history log).

## Tech Stack

**Backend** (`backend/`) — Python 3.12
- **FastAPI** — REST API layer (`api.py`)
- **Uvicorn** — ASGI server
- **Pydantic v2** — request/response validation
- **SQLAlchemy 2.0** — ORM (typed `Mapped` models)
- **Alembic** — database migrations (`backend/migrations/`)
- **PostgreSQL 17** via **psycopg 3** — primary datastore

**Frontend** (`frontend/`) — Node / ES modules
- **React 19** — UI (single-page dashboard in `src/`)
- **Vite** — dev server & build tooling
- **Tailwind CSS v4** (`@tailwindcss/vite`) — styling
- **ESLint** — linting

**Domain logic** — combat resolution lives in `backend/game/` (to-hit
calculations, range brackets, hit-location and cluster tables), decoupled from
the API so the placeholder rules can be swapped for full BattleTech rules.

---

## Running with Docker (recommended)

The whole stack — database, backend API, and frontend — runs with a single
command. You only need Docker and Docker Compose installed.

### 1. Configure credentials

Copy the example environment file and adjust if you like (the defaults work
out of the box):

```
cp .env.example .env
```

`.env` holds the Postgres credentials shared by the `db` and `backend`
services. It is gitignored so your credentials never get committed.

### 2. Start everything

```
docker compose up --build
```

This will:
- Start **PostgreSQL 17** (`db` service) with a persistent named volume
- Build and start the **backend** — it runs `alembic upgrade head` automatically
  before the API comes up, so the schema is always current
- Build and start the **frontend** — nginx serves the built React app and
  proxies `/api/*` to the backend

Once it's up:
- **App:** http://localhost
- **API (direct, for debugging):** http://localhost:8000

### 3. Stopping

```
docker compose down        # stop containers, keep the database
docker compose down -v     # stop AND wipe the database volume (destroys data)
```

Your data lives in the `db_data` volume and survives normal restarts and
rebuilds. Only `down -v` (or manually removing the volume) clears it.

---

## Database Backup & Seeding

The app can dump its entire database to a **seed file** so another machine
comes up pre-populated on first launch.

### Creating a backup

1. In the running app, click the **⚙️ gear icon** (top-right corner).
2. Choose **Backup Database**.

This runs `pg_dump` inside the backend container and writes the result to
`db_seed/seed.sql` on the host (the `db_seed/` directory is bind-mounted into
both the backend and the database containers).

### How another machine gets seeded

1. Commit the generated dump so it travels with the repo:
   ```
   git add db_seed/seed.sql && git commit -m "Update database seed"
   ```
2. On the other machine, run `docker compose up --build`.

On **first boot with an empty database volume**, PostgreSQL automatically runs
any `.sql` file in its init directory (`db_seed/` is mounted there), so
`seed.sql` loads and the database is seeded. The backend's `alembic upgrade
head` then sees the schema is already at head and does nothing — no conflict.

> **Important:** Auto-seeding only happens on a *fresh* database volume. If the
> target machine already has a populated `db_data` volume, the seed file is
> **not** re-applied. To force a clean re-seed, run `docker compose down -v`
> first (this wipes existing data).

---

## Local development (without Docker)

Useful for backend debugging with breakpoints or a fast frontend dev loop.

### Database

Run a standalone Postgres container (matches the compose credentials):

```
docker run --name local-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -p 5432:5432 -d postgres:17
```

### Backend

Use `pyenv` (or any Python 3.12) then:

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

# Apply migrations, then start the API
alembic upgrade head
python3 api.py
```

The API defaults to `postgresql+psycopg://postgres:mysecretpassword@localhost:5432/postgres`.
Override it by setting the `DATABASE_URL` environment variable.

### Frontend

```
cd frontend
npm install
npm run dev
```

For local dev the frontend reads `VITE_API_URL` (see `frontend/.env.local`,
which defaults to `http://localhost:8000`). Inside Docker this is unset and the
app uses relative URLs proxied by nginx instead.

---

## Future Schema Changes

Whenever you need to modify the database schema (e.g., adding a column):

1. Generate a new script: `alembic revision -m "add ammo column"`
2. Edit the script's `upgrade()` function, e.g. `op.add_column(...)`.
3. Apply it: `alembic upgrade head`

Inside Docker, migrations run automatically on backend startup, so a new
migration is applied the next time you `docker compose up`.
