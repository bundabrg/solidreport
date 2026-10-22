import psycopg2

from models.config import Config

# Cache of SQL fragments per connection (see time_work_filter)
_work_filter_cache = {}


def database(cfg: Config):
    # Load Database
    return psycopg2.connect(
        dsn=f"host={cfg.db.host} dbname={cfg.db.database} user={cfg.db.username} password={cfg.db.password}"
    )


def time_work_filter(db) -> str:
    """
    SQL fragment restricting time_entries rows to actual work.

    Solidtime 0.22 introduced a 'type' column ('work'/'break') on time_entries
    and stores breaks as time_entries rows themselves. Schemas without the
    column must not reference it, so the fragment is detected once per
    connection and cached.
    """
    key = id(db)
    fragment = _work_filter_cache.get(key)
    if fragment is None:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM information_schema.columns"
                " WHERE table_name = 'time_entries' AND column_name = 'type'"
            )
            fragment = "AND te.type = 'work'" if cursor.fetchone() is not None else ""
        _work_filter_cache[key] = fragment
    return fragment
