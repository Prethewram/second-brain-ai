# Database migrations

The backend uses Alembic. Run commands from `backend`; the application reads
`DATABASE_URL` from its environment/settings. No credentials are stored in
`alembic.ini`.

```console
python -m alembic upgrade head
python -m alembic upgrade head --sql
```

Stabilization repaired the initial users revision so an empty database can be
created through migrations. Existing databases already stamped beyond that
revision do not rerun it. No migrations were run against the development database.

The legacy memory migration copies `value` into `content` before enforcing
non-null constraints and sets `source` to `chat`. Downgrading preserves text in
`value`, but the previously dropped legacy `key` cannot be recovered: generated
keys use `memory_<id>`. Migration tests exercise this on a disposable database.

Do not stamp or downgrade an existing database to repair migration history
without first inspecting its schema and backing up its data.
