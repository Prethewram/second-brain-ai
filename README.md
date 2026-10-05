# Second Brain AI

A FastAPI backend for personal memories, notes, tasks, profiles, and AI chat.
Data is stored in PostgreSQL. Authenticated chat uses Gemini to extract actions,
save supported information, and respond using the user's stored context.
The project includes a React + TypeScript frontend built with Vite and a FastAPI API.
Meetings / MOM captures meeting dates, attendees, agendas, minutes, and decisions,
with linked notes and tasks that also appear in the main library. This workflow
works without AI requests.

## Frontend

After starting the backend below, open another terminal with Node.js 24 installed:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173` to create an account, chat, and manage your library.
The Vite proxy connects it to the backend at port 8000.
See [the frontend guide](frontend/README.md) for browser tests and hosting setup.

## Local setup (Windows PowerShell)

Prerequisites: Git, Python 3.12, and a running PostgreSQL 16 server. The commands
below use the Windows Python launcher and run from the repository directory.
Live AI requests also need your own Gemini API key.

```powershell
git clone https://github.com/Prethewram/second-brain-ai.git
cd second-brain-ai\backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

If you already have this checkout, start with `cd backend` and skip cloning.
Edit `backend/.env`: set your local PostgreSQL password, paste the generated
value into `SECRET_KEY`, and supply `GEMINI_API_KEY`. Keep `ALGORITHM=HS256` and
`ENABLE_DEV_ENDPOINTS=false`. Passwords with special characters must be URL-encoded
in `DATABASE_URL`. Real `.env` files are ignored by Git; `.env.example` contains
placeholders only. Existing process environment variables override `.env` values.

Create an empty database named `second_brain` using pgAdmin, or use this command
if PostgreSQL's `psql` is on your PATH:

```powershell
psql -U postgres -h localhost -c "CREATE DATABASE second_brain;"
```

Use an existing database only after reviewing its schema and migration history.
From `backend`, apply migrations and start the development server:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open [the health response](http://127.0.0.1:8000/) and
[interactive API documentation](http://127.0.0.1:8000/docs).
The root response should be `{"message":"Second Brain AI Backend Running"}`.
`--reload` is for local development.

## Try the API

With the server running, open a second PowerShell terminal. Register and log in
with JSON requests, then use the returned bearer token:

```powershell
$baseUrl = "http://127.0.0.1:8000"
$registration = @{ name = "Demo User"; email = "demo@example.com"; password = "local-demo-password" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$baseUrl/auth/register" -ContentType "application/json" -Body $registration

$credentials = @{ email = "demo@example.com"; password = "local-demo-password" } | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri "$baseUrl/auth/login" -ContentType "application/json" -Body $credentials
$headers = @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod -Uri "$baseUrl/users/me" -Headers $headers

$message = @{ message = "Remember that I prefer morning meetings." } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$baseUrl/chat" -Headers $headers -ContentType "application/json" -Body $message
```

The chat response includes `conversation_id` and `response`. Include that
`conversation_id` with the next message to continue the conversation. Chat makes
live Gemini requests, so it requires a valid key and may incur provider usage.
`POST /ai/analyze` returns suggested actions and a reply without executing actions.
The login endpoint accepts JSON; the Swagger OAuth password form sends form data,
so use the JSON login example above to obtain a token.

## How requests work

1. Registration stores a bcrypt password hash; login returns an expiring JWT.
2. Protected endpoints validate the token and enforce ownership of stored records.
3. Chat saves the user's message, analyzes it, and executes supported actions:
   `memory.create`, `note.create`, `task.create`, and `profile.update`.
4. The reply uses conversation history and stored user context, then is saved.

AI extraction depends on the model's response. Saved data is also accessible
through authenticated CRUD endpoints under `/memory`, `/notes`, `/tasks`, and
`/profile`. See the interactive API documentation for request fields.

## Checks and tests

Run these commands from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check app tests alembic scripts
.\.venv\Scripts\python.exe -m black --check app tests alembic scripts
.\.venv\Scripts\python.exe -m pytest -q --cov=app --cov-report=term-missing
```

The default test suite uses isolated SQLite databases and skips three PostgreSQL
migration tests. Tests supply their own credentials and block live Gemini calls.
GitHub Actions runs the complete suite against disposable PostgreSQL 16, including
the migrations, with an 80% coverage floor. For local PostgreSQL testing, see
[the test guide](backend/tests/README.md).

## Troubleshooting

- **Missing settings:** run from `backend`, copy `.env.example` to `.env`, and
  replace its placeholders.
- **Database connection refused:** start PostgreSQL and check the host, port,
  username, password, and database name in `DATABASE_URL`.
- **Tables do not exist:** run `alembic upgrade head` against the intended database.
- **401 response:** log in again and send `Authorization: Bearer <access_token>`.
- **Gemini request fails:** check your API key, model access, and provider quota.

Further documentation: [API behavior](docs/api.md),
[database migrations](docs/database.md), and [backend tests](backend/tests/README.md).
