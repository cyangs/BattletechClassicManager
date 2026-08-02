# BattleTech Classic Manager

A campaign/session manager for BattleTech Classic — a mech & weapon library plus
game sessions with turn-based weapon-fire resolution (to-hit rolls, hit
locations, per-session weapon state, and an event history log).

## Tech Stack

**Backend** (`backend/`) — Python 3.14
- **FastAPI** — REST API layer (`api.py`)
- **Uvicorn** — ASGI server
- **Pydantic v2** — request/response validation
- **SQLAlchemy 2.0** — ORM (typed `Mapped` models)
- **Alembic** — database migrations (`backend/migrations/`)
- **PostgreSQL** via **psycopg 3** — primary datastore

**Frontend** (`frontend/`) — Node / ES modules
- **React 19** — UI (single-page dashboard in `src/`)
- **Vite** — dev server & build tooling
- **Tailwind CSS v4** (`@tailwindcss/vite`) — styling
- **ESLint** — linting

**Domain logic** — combat resolution lives in `backend/game/` (to-hit
calculations, range brackets, hit-location and cluster tables), decoupled from
the API so the placeholder rules can be swapped for full BattleTech rules.

## Future Schema Changes

Whenever you need to modify your database in the future (e.g., adding an ammo_type column to your
weapons table), you simply repeat the cycle:

Run `alembic revision -m "add ammo column"` to generate a new script.

Edit the script's upgrade() function with op.add_column(...).

Run `alembic upgrade head` to apply it.

## Database

```
docker run --name local-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d postgres
```


## Running - 

### Backend - 

TODO: I need to put this up or container this. What a fucking nightmare. 

use `pyenv` to install `python3.14` then do the below. 

Create virtual environment

`python3 -m venv .venv`

`source .venv/bin/activate`

May need to pip install <something>
`ModuleNotFoundError: No module named 'fastapi'`
`ModuleNotFoundError: No module named 'uvicorn'`

`python3 -m pip install -r requirements.txt`

`python3 api.py
`

### Frontend - 

`npm install`

`npm run dev`
