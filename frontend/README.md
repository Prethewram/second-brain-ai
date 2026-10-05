# Second Brain frontend

React, TypeScript, and Vite, with Lucide icons and responsive CSS. The interface
connects to the FastAPI backend; it does not ship with sample user data.

## Run locally

Use Node.js 24 LTS. Start the backend at `http://127.0.0.1:8000` using the
[root setup guide](../README.md), then open a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. Register an account or sign in, then use the thinking
space and library. Vite forwards `/api/*` to the backend and removes `/api`.
This keeps browser requests on the same origin and needs no backend CORS change.
The development server binds to loopback only.

The bearer token is stored in `sessionStorage` for this browser tab. Refreshes
validate it against `/users/me`; an expired token signs you out. Signing out
clears the token and in-memory user data. Chat history stays available while
switching screens, but a page reload starts a new frontend conversation because
the backend does not currently expose conversation-history retrieval.

## Features

- JSON registration/login and authenticated requests.
- Chat with conversation continuity, new conversations, pending/error states,
  and library refresh after a reply.
- Readable reply cards with Markdown headings, lists, tables, and code blocks,
  plus a copy-reply button. Raw HTML is disabled and unsafe link schemes are
  filtered by the Markdown renderer.
- Notes: create, edit, archive, restore, delete, and search.
- Tasks: create, edit, complete, delete, search, and completed-item filtering.
- Memories: search, edit, and delete; new memories are extracted through chat.
- Profile: create/update supported fields and delete the profile.
- Meetings / MOM: capture structured minutes, edit meetings, and add linked notes
  and tasks. Complete tasks from the meeting; deleting a meeting keeps its notes
  and tasks in the library. No Gemini request is needed.
- Responsive navigation, accessible labels, keyboard-friendly dialogs,
  deletion confirmation, empty states, and request retry.

The backend saves the user message before generating a reply. If chat fails,
some data may already be saved; the UI explains that instead of silently retrying
a potentially duplicated action. Completing a task is one-way in the current API.

## Verify

```powershell
npm run build
npm run format:check
npx playwright install chromium
npm test
```

The production build includes TypeScript checking. Browser tests mock API calls
and exercise authentication, note lifecycle, task completion, profile saving,
conversation continuity, expired sessions, retry, and mobile layout. They never
call Gemini or touch your database. A meeting workflow test covers creation,
linked notes/tasks, completion, editing, and preservation after deletion.
Generated reports and screenshots are ignored
by Git. Backend integration tests separately verify real API behavior.

## Production hosting

`npm run build` writes static assets to `dist`. Your production web server must
serve these files and forward `/api/*` to FastAPI, removing the `/api` prefix,
as the Vite development proxy does. `npm run preview` previews static assets;
it is not a production API server. Never put a Gemini key or JWT signing secret
in frontend environment variables or JavaScript bundles.

Typography uses Google Fonts with local sans-serif fallbacks. The application
remains usable if those font requests are unavailable.
