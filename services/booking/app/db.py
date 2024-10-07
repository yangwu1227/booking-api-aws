from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def get_local_session() -> sessionmaker:
    """
    Create a SQLAlchemy session maker.

    This function creates a SQLAlchemy engine using the database URL from the configuration and returns a sessionmaker instance.
    A sessionmaker is responsible for generating new session objects, which are used to interact with the database.

    For more information, see the SQLAlchemy documentation on:

    - Engine: https://docs.sqlalchemy.org/en/20/core/engines.html
    - Session: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#using-a-sessionmaker

    Returns
    -------
    sessionmaker
        A SQLAlchemy sessionmaker instance, which can be used to create database sessions.
    """
    settings = get_settings()
    database_url = settings.database_url
    engine = create_engine(database_url)

    # Create a sessionmaker bound to the engine
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_local


def get_database_session() -> Generator[Session, None, None]:
    """
    Dependency to provide a database session for FastAPI requests, declared for all endpoints: submit, list, accept, and reject.

    This function generates a new SQLAlchemy session for each incoming FastAPI request. The session is yielded,
    allowing the request to use the same session throughout its lifecycle. After the request is completed,
    the session is closed to ensure the database connection is properly managed.

    For more information on SQLAlchemy sessions, see:
    https://docs.sqlalchemy.org/en/20/orm/session_basics.html#using-a-sessionmaker

    Yields
    -------
    Session
        A SQLAlchemy session object, which can be used to interact with the database.
    """
    session_local = get_local_session()
    database_session = session_local()

    try:
        yield database_session
    finally:
        database_session.close()
