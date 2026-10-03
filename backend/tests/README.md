# Backend tests

Run from `backend` with a working Python environment:

```console
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The shared fixtures replace database and AI credentials before importing the
application. Each `db_session` gets its own in-memory SQLite database with foreign
keys enabled. Committed rows disappear when that fixture ends. The `client`
fixture overrides `get_db` and restores dependency overrides after use.

Live Gemini generation is blocked; chat tests must inject a fake AI client or
mock the provider. Unit tests do not need to import the FastAPI application.

SQLite validates service behavior and fixture isolation. Without PostgreSQL,
the three live migration tests are skipped; offline SQL generation still runs.

Set `TEST_POSTGRES_URL` to a disposable PostgreSQL database whose name ends in
`_test` to run the full suite on PostgreSQL. Each test gets a uniquely named schema;
cleanup removes only that schema. Migration tests verify a fresh schema against
the ORM models, downgrade/re-upgrade, and upgrading populated legacy memories.
Never supply a development or production database, even if its name ends in `_test`.

On Windows with PostgreSQL 16 installed, the local helper creates a private
cluster on an unused loopback port and stops it after testing:

```console
.test-venv\Scripts\python.exe scripts\run_postgres_tests.py --postgres-bin "C:\Program Files\PostgreSQL\16\bin"
```

Install `requirements-dev.txt` for lint and format checks:

```console
python -m ruff check app tests alembic scripts
python -m black --check app tests alembic scripts
python -m pytest -q --cov=app --cov-report=term-missing --cov-report=xml
```

GitHub Actions runs these checks and the complete PostgreSQL suite on pushes
and pull requests. Coverage includes statements and branches, with an 80% minimum.
Unexpected warnings fail tests, except Passlib's known Python 3.12 Unix `crypt`
import deprecation (password hashing uses bcrypt). The intentionally malformed Pydantic model
test explicitly checks its expected warning. The local PostgreSQL helper disables
pytest's cache plugin to avoid Windows permissions conflicts between run users.

The development action endpoint is disabled by default. Explicitly set
`ENABLE_DEV_ENDPOINTS=true` for local development to enable it; authentication is
still required, and actions belong to the caller. It is hidden from the API schema.

ActionEngine rolls back a failed action's pending transaction before continuing.
Earlier actions that already committed remain saved. If rollback itself fails,
execution stops and the failure propagates rather than using a broken session.

For the local fallback environment created during stabilization:

```console
.test-venv\Scripts\python.exe -m pytest -q
```
