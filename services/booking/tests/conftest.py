from copy import deepcopy
from pathlib import Path
from typing import Generator

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

alembic_config = Config(str(Path(__file__).parents[1] / "migrations" / "alembic.ini"))
alembic_config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))


@pytest.fixture(scope="session")
def database() -> None:
    """
    Fixture to create and manage a test database for the session.

    This fixture connects to the PostgreSQL instance using the `psycopg` library,
    drops the existing database (if it exists), and creates a fresh database
    for testing. It ensures that a clean database is available for the entire
    test session.

    The fixture does not return any values but performs database creation and
    setup at the start of the test session.

    Returns
    -------
    None
    """
    # Create a copy of the database URL to avoid modifying the original settings
    database_url = deepcopy(get_settings().database_url)
    # Extract the database name from the URL
    database_name = database_url.split("/")[-1]
    # Connect to the default database since we cannot drop the test database that we are connected to, i.e., `database_name`
    admin_url = database_url.rsplit("/", 1)[0] + "/postgres"
    admin_url = admin_url.replace("postgresql+psycopg", "postgresql")

    # Drop the existing database and create a new one at the start of the test session
    with psycopg.connect(admin_url) as conn:
        # Allow execution of DROP/CREATE DATABASE outside transactions
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {database_name}")
            cur.execute(f"CREATE DATABASE {database_name}")


@pytest.fixture(scope="session")
def database_session(database) -> Generator[Session, None, None]:
    """
    Fixture to create a SQLAlchemy session for interacting with the test database.

    This fixture depends on the `database` fixture, ensuring that the test
    database is created before initializing the SQLAlchemy session. It sets up
    an engine using the test database URL and binds it to the session. The
    database schema is created via SQLAlchemy's ORM at the start of the session,
    and all tables are dropped at the end of the session for cleanup.

    Parameters
    ----------
    database : None
        The `database` fixture ensures that the test database is created before
        establishing a session.

    Yields
    ------
    sqlalchemy.orm.Session
        A SQLAlchemy session connected to the test database, used to perform
        transactions within the test session.
    """
    database_url = get_settings().database_url
    engine = create_engine(database_url)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    database_session = session_local()
    command.upgrade(alembic_config, "head")
    yield database_session
    database_session.close()
    command.downgrade(alembic_config, "base")
    engine.dispose()
