# Authentication

`POST /auth/register` accepts `name`, `email`, and `password`; successful responses
contain only `id`, `name`, and `email`. Passwords are hashed and never returned.
Names are trimmed and must fit the 100-character database column. Passwords must
be nonempty and at most 72 UTF-8 bytes, matching bcrypt's supported input length.
Duplicate registration returns 400, including when another request wins the
database uniqueness race; the failed transaction is rolled back.

`POST /auth/login` accepts email and password and returns `access_token` and
`token_type: bearer`. Wrong passwords and nonexistent users both return 401 with
`Invalid credentials`. Overlong login passwords are rejected without truncation.

Use `Authorization: Bearer <access_token>` for protected routes, including
`GET /users/me`. Tokens must have a valid signature, a future `exp`, and a numeric
`sub` identifying an existing user. Missing, malformed, expired, and deleted-user
tokens return 401. Invalid numeric subjects are rejected before querying the
database. Authentication errors include the `WWW-Authenticate: Bearer` header.

The existing successful registration and login response schemas are unchanged.

## AI analysis

`POST /ai/analyze` requires a bearer token and a nonempty `message` string.
Unauthenticated requests return 401; malformed or blank messages return 422 before
calling the AI provider. Successful responses retain the existing `actions` and
`reply` fields. This endpoint analyzes only; it does not execute extracted actions.
Clients that previously called it anonymously must now supply an access token.

## AI provider failures

Provider overload and quota failures return 503 with a safe explanation instead
of a generic 500. Configuration failures return 502. Raw provider errors and
credentials are not included in API responses. The SDK handles transient retries
inside the provider call; the application does not replay chat actions.

When `/chat` fails after saving a message, its error `data` includes
`conversation_id`, `message_saved: true`, and `actions_may_be_saved`.
The frontend keeps this conversation ID for the next message, shows the actual
cause, and refreshes the library. An analysis failure sets `actions_may_be_saved`
to false; a reply failure sets it to true if extracted actions were attempted.
There is no fabricated assistant reply and no automatic resubmission of the chat
request. Provider downtime still requires waiting for the provider to recover.

The AI client switches to `GEMINI_FALLBACK_MODEL` if the primary model returns
408/500/502/503/504 or its connection fails. The default fallback is
`gemini-3.1-flash-lite`; set it to an empty string to disable it. Configuration,
permission, and quota errors do not switch models. Each model request has a
30-second timeout and at most two SDK attempts. Only generation is retried;
database writes and action execution are not replayed. Both models use the
same Gemini API key, and fallback responses may differ in quality.
