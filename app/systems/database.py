import psycopg2

from models.config import Config


def database(cfg: Config):
    # Load Database
    return psycopg2.connect(
        dsn=f"host={cfg.db.host} dbname={cfg.db.database} user={cfg.db.username} password={cfg.db.password}"
    )
