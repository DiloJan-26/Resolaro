from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from resolaro.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return create_engine(url, pool_size=2, max_overflow=0, pool_timeout=5, pool_recycle=1800, pool_pre_ping=True)


def get_session():
    factory = sessionmaker(bind=get_engine(), class_=Session, expire_on_commit=False)
    with factory() as session:
        yield session
