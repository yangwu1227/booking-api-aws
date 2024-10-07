import logging
import secrets
import string
import sys
from argparse import ArgumentParser

import boto3
from botocore.exceptions import ClientError
from mypy_boto3_secretsmanager import SecretsManagerClient
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(name="manage_passwords")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def generate_strong_password() -> str:
    """
    Generate a strong random password.

    Returns
    -------
    str
        The generated strong password.
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(characters) for _ in range(16))


def store_password(sm_client: SecretsManagerClient, secret_name: str, password: str) -> None:
    """
    Store the password in AWS Secrets Manager.

    Parameters
    ----------
    sm_client: SecretsManagerClient
        The Secrets Manager client.
    secret_name : str
        The name of the secret in AWS Secrets Manager.
    password : str
        The password to store.

    Raises
    ------
    ClientError
        If storing the secret in Secrets Manager fails.
    """
    try:
        sm_client.put_secret_value(SecretId=secret_name, SecretString=password)
        logger.info(f"Password updated in Secrets Manager for {secret_name}")
    except ClientError as e:
        logger.error(f"Failed to update secret: {e}")
        raise


def get_db_connection_string(sm_client: SecretsManagerClient, secret_name: str) -> str:
    """
    Fetch the database connection string from AWS Secrets Manager.

    Parameters
    ----------
    sm_client: SecretsManagerClient
        The Secrets Manager client.
    secret_name : str
        The name of the secret in AWS Secrets Manager.

    Returns
    -------
    str
        The database connection string.

    Raises
    ------
    ClientError
        If fetching the secret fails.
    """
    try:
        secret = sm_client.get_secret_value(SecretId=secret_name)
        return secret["SecretString"]
    except ClientError as e:
        logger.error(f"Failed to retrieve DB connection string: {e}")
        raise


def upsert_user_password(
    db_connection_string: str, username: str, hashed_password: str, role: str, disabled: bool
) -> None:
    """
    Insert or update the user password in the database using SQLAlchemy.

    Parameters
    ----------
    db_connection_string : str
        The database connection string.
    username : str
        The username for which the password should be updated or inserted.
    hashed_password : str
        The new hashed password.
    role : str
        The role of the user (e.g., admin, requester).
    disabled : bool
        Whether the user account is disabled.
    """
    engine = create_engine(db_connection_string)
    try:
        with engine.connect() as conn:
            with conn.begin():
                query = text(
                    """
                    INSERT INTO users (username, hashed_password, role, disabled)
                    VALUES (:username, :hashed_password, :role, :disabled)
                    ON CONFLICT (username) 
                    DO UPDATE SET 
                        hashed_password = EXCLUDED.hashed_password, 
                        role = EXCLUDED.role, 
                        disabled = EXCLUDED.disabled
                """
                )
                conn.execute(
                    query,
                    {
                        "username": username,
                        "hashed_password": hashed_password,
                        "role": role,
                        "disabled": disabled,
                    },
                )
            logger.info(f"Password updated or inserted in DB for user: {username}")
    except SQLAlchemyError as error:
        logger.error(f"Failed to update password in DB: {error}")
        raise


def manage_passwords(
    env: str, sm_client: SecretsManagerClient, username: str, role: str, disabled: bool
) -> None:
    """
    Rotate passwords for a specified user, store it in AWS Secrets Manager,
    and update the password in the database.

    Parameters
    ----------
    env : str
        The deployment environment (e.g., 'dev' or 'prod').
    sm_client: SecretsManagerClient
        The Secrets Manager client.
    username : str
        The username whose password is being rotated.
    role : str
        The role of the user (e.g., 'admin', 'requester').
    disabled : bool
        Whether the user account is disabled.
    """
    try:
        # Generate new password
        password = generate_strong_password()
        # Store password in Secrets Manager
        store_password(sm_client, f"{username}_password_{env}", password)
        # Fetch the DB connection string from Secrets Manager
        db_connection_string = get_db_connection_string(sm_client, f"db_connection_string_{env}")
        # Hash password before storing in DB
        pwd_context = CryptContext(schemes=["bcrypt"])
        hashed_password = pwd_context.hash(password)
        # Update password in the database
        upsert_user_password(db_connection_string, username, hashed_password, role, disabled)
        logger.info(f"Password rotation completed successfully for {username} in {env}")
    except Exception as error:
        logger.error(f"Password rotation failed for {username} in {env}: {error}")
        raise


def main() -> int:

    parser = ArgumentParser(
        description="Rotate passwords and update AWS Secrets Manager and Database"
    )
    parser.add_argument(
        "--env", type=str, required=True, help="The deployment environment (e.g., 'dev' or 'prod')"
    )
    parser.add_argument(
        "--username", type=str, required=True, help="The username whose password should be rotated"
    )
    parser.add_argument(
        "--role", type=str, required=True, help="The role of the user (e.g., 'admin', 'requester')"
    )
    parser.add_argument(
        "--disabled", action="store_true", help="Whether the user account is disabled."
    )
    args, _ = parser.parse_known_args()
    sm_client: SecretsManagerClient = boto3.client("secretsmanager")
    manage_passwords(
        env=args.env,
        sm_client=sm_client,
        username=args.username,
        role=args.role,
        disabled=args.disabled,
    )

    return 0


if __name__ == "__main__":

    main()
