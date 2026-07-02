## Future Schema Changes

Whenever you need to modify your database in the future (e.g., adding an ammo_type column to your
weapons table), you simply repeat the cycle:

Run `alembic revision -m "add ammo column"` to generate a new script.

Edit the script's upgrade() function with op.add_column(...).

Run `alembic upgrade head` to apply it.

## Database

docker run --name local-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  -d postgres

## Running - 

`python api.py
`