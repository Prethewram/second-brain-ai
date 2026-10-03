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
