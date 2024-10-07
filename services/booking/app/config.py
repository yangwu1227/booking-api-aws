import os
from functools import lru_cache
from typing import Optional

import boto3
from pydantic_settings import BaseSettings


class BaseAppSettings(BaseSettings):
    """
    Base settings for the application.

    Attributes
    ----------
    environment : str
        The environment the application is running in.
    testing : bool
        Whether the application is running in test mode.
    debug : bool
        Whether the application is running in debug mode.
    _database_url : Optional[str]
        The database connection string. Default is None.
    """

    environment: str
    testing: bool = False
    debug: bool = False
    _database_url: Optional[str] = None

    @property
    def database_url(self) -> str:
        """
        Fetches the database connection string from AWS Secrets Manager.

        Returns
        -------
        str
            The database connection string.
        """
        if self._database_url is None:
            sm = boto3.client("secretsmanager")
            self._database_url = sm.get_secret_value(
                SecretId=f"db_connection_string_{self.environment}"
            )["SecretString"]
        return self._database_url


class TestSettings(BaseAppSettings):
    """
    Test settings, inheriting from BaseAppSettings.

    Attributes
    ----------
    environment : str
        Overriden to "test" so the test database connection string is fetched.
    testing : bool
        Overriden to True so the application runs in test mode.
    debug : bool
        Overriden to True so the application runs in debug mode.
    """

    environment: str = "test"
    testing: bool = True
    debug: bool = True

    @property
    def database_url(self) -> str:
        """
        Returns the test database connection string.

        Returns
        -------
        str
            The test database connection string.
        """
        if self._database_url is None:
            test_database_url = os.getenv("DATABASE_URL_TEST")
            if test_database_url:
                self._database_url = test_database_url
            else:
                raise ValueError("DATABASE_URL_TEST environment variable not set")
        return self._database_url


@lru_cache()
def get_settings() -> BaseAppSettings:
    """
    Returns the settings based on the environment the application is running in.

    Returns
    -------
    BaseAppSettings
        An instance of a subclass of BaseAppSettings.
    """
    env = os.getenv("ENV", None)
    match env:
        case "dev":
            return BaseAppSettings(environment="dev", debug=True, testing=False)
        case "prod":
            return BaseAppSettings(environment="prod", debug=False, testing=False)
        case "test":
            return TestSettings(environment="test", debug=True, testing=True)
        case _:
            raise ValueError(f"Invalid ENV environment variable: {env}")
