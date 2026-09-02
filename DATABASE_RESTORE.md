# Database: retired, and how to bring it back

**Status as of 2026-09-02: this project has no live database.** The Neon
(Lakebase Postgres) project that backed it was deleted to stop it sitting in the
monthly bill. It had been dormant since the last commit here, 2026-01-25.

Nothing was lost. A full verified dump was taken immediately before deletion.
The app is not broken in any way that a restore won't fix.

## Where the backup is

It is **not in this repo** (it contains user rows, so it stays off a public
remote). On Lee's machine:

```
~/backups/neon-sticker-maker-20260902/
├── neondb-production.dump     # pg_dump custom format — restore with pg_restore
├── neondb-production.sql      # same data, plain SQL
├── neondb-development.dump    # the dev branch — it was empty
├── neondb-development.sql
└── RESTORE.md                 # full detail, incl. the old Neon project/branch IDs
```

That `RESTORE.md` is the authoritative copy and has the account-specific
identifiers. This file is the pointer, so that anyone opening this repo cold
knows the backup exists.

## What is in the dump

| Table | Rows |
|---|---|
| `stickers` | 16 |
| `users` | 1 |
| `alembic_version` | 1 |

Verified with `pg_restore -l` (all tables, sequences, PKs, and the
`stickers.creator -> users` FK are present) and by counting the rows inside the
`COPY` blocks, not just by checking the file was non-empty.

**Sticker images are not in the database.** `stickers.image_path` holds local
filesystem paths like `fastapp/workspace/output/74a8.png`, relative to a
checkout of this repo. Nothing was in cloud object storage, so the dump plus
this repo is the whole picture. If that `workspace/output` directory is gone,
the image files are gone with it — the DB rows will still restore, they will
just point at paths that no longer resolve.

Most rows are `status='error'` from the last session in January: an expired
Replicate API token, and the storefront rejecting `payment_methods.0`. Only a
few are `status='ready'`.

## Restoring

You need `pg_dump`/`pg_restore`. They are not in a default macOS install:

```bash
brew install libpq
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"   # keg-only, not linked by default
```

### 1. Create a new Postgres

Any Postgres works. To go back to Neon:

```bash
npx neon@latest projects create --name stickermaker --region-id aws-us-east-2
npx neon@latest connection-string <branch> --project-id <new-project-id>
```

Or run it locally with the `docker-compose.yml` in this repo, which is cheaper
if you are just poking at old data.

### 2. Restore the dump

```bash
cd ~/backups/neon-sticker-maker-20260902
pg_restore -d "<connection-string>" --no-owner --no-privileges neondb-production.dump
```

`--no-owner --no-privileges` matters: the dump was taken as `neondb_owner`, a
role that will not exist in the new database.

Plain-SQL alternative: `psql "<connection-string>" -f neondb-production.sql`

### 3. Point the app at it

`fastapp/services/db.py` prefers `DATABASE_URL` over everything else, so set it
in `.env` (which is gitignored) and the app picks it up with no code change:

```
DATABASE_URL=postgresql://...
```

### 4. Migrations

`alembic_version` is preserved in the dump, so migrations resume from the
correct revision instead of trying to replay from scratch:

```bash
cd fastapp/db
alembic upgrade head
```

## If you would rather start clean

Skip the restore entirely — create the database, set `DATABASE_URL`, and run
`alembic upgrade head` against an empty database. The schema builds itself. You
lose 16 sticker rows, most of which recorded failures anyway.
