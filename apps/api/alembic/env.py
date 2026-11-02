import os
import re

from alembic import context
from sqlalchemy import create_engine, text

from resolaro.models import Base

target_metadata = Base.metadata


def run_migrations_online() -> None:
    url = os.environ.get("MIGRATION_DATABASE_URL")
    schema = os.environ.get("MIGRATION_SCHEMA")
    if not url or not schema or not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", schema):
        raise RuntimeError("MIGRATION_DATABASE_URL and a safe MIGRATION_SCHEMA are required")
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    engine = create_engine(url, pool_size=1, max_overflow=0, pool_pre_ping=True)
    with engine.connect() as connection:
        connection.execute(text(f'SET search_path TO "{schema}"'))
        connection.commit()
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
