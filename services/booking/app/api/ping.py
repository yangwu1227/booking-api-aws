from pathlib import Path
from typing import Dict

from alembic import config, script
from alembic.runtime import migration
from fastapi import APIRouter, Response
from sqlalchemy import create_engine

from app.config import get_settings

router = APIRouter()


@router.get("/ping/", response_model=Dict[str, str])
async def ping(response: Response) -> Dict[str, str]:
    """
    Health check endpoint that verifies the database's migration status.

    This endpoint checks if the current database schema is up-to-date by comparing
    the current migration revision with the latest migration in the Alembic migrations
    directory.

    If the database is not in sync with the latest Alembic migration, it returns a 400
    status code with an appropriate message. If the database is up-to-date, it returns
    a success response with "ok".

    This ensures that the fargate task will not start receiving traffic until the the standalone
    migration container has finished running the migrations.

    Parameters
    ----------
    response : Response
        The response object.

    Returns
    -------
    Dict
        A dictionary containing the message "ok".
    """
    settings = get_settings()
    database_url = settings.database_url
    engine = create_engine(database_url)

    # Path relative to the current file
    alembic_config = config.Config(str(Path(__file__).parents[2] / "migrations" / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(Path(__file__).parents[2] / "migrations"))
    migration_script = script.ScriptDirectory.from_config(alembic_config)

    with engine.connect() as conn:
        context = migration.MigrationContext.configure(conn)
        # Check if the current revision is the latest
        if context.get_current_revision() != migration_script.get_current_head():
            response.status_code = 400
            return {"message": "Database is not up-to-date yet"}
    return {"message": "ok"}
