import os
from base64 import b64decode
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Dict, Optional, Union

import boto3
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_database_session
from app.models.db_models import User

ALGORITHM = "EdDSA"
ENV = os.getenv("ENV")

# In test mode, we don't need to fetch the secrets from aws secrets manager since we mock the authentication
if ENV == "test":
    PUBLIC_KEY, PRIVATE_KEY = "test_public_key", "test_private_key"
# In dev or prod mode, fetch the secrets from aws secrets manager
elif ENV in ["dev", "prod"]:
    sm = boto3.client("secretsmanager")
    # Secret and algorithm settings
    PUBLIC_KEY = b64decode(
        sm.get_secret_value(SecretId=f"public_key_{ENV}")["SecretString"]
    ).decode("utf-8")
    PRIVATE_KEY = b64decode(
        sm.get_secret_value(SecretId=f"private_key_{ENV}")["SecretString"]
    ).decode("utf-8")
    sm.close()
else:
    raise RuntimeError("Unknown environment: Please set 'ENV' to 'test', 'dev', or 'prod'")

# Password hashing context and OAuth2 scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    """
    Model representing the JWT token returned after successful authentication.

    Attributes
    ----------
    access_token : str
        The JWT access token used for authentication and authorization.
    token_type : str
        The type of the token, typically "bearer" for OAuth2 token types.
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Model representing the data extracted from a JWT token, typically for identifying the user.

    Attributes
    ----------
    username : str
        The username or identifier of the user extracted from the token.
        This is typically stored in the 'sub' field of the JWT payload.
    """

    username: str


class UserDetails(BaseModel):
    """
    Model representing the user profile with basic details.

    Attributes
    ----------
    username : str
        The unique username of the user.
    disabled : Optional[bool]
        Indicates whether the user account is disabled. If True, the user cannot log in.
    role : Optional[str]
        The role of the user (e.g., "admin", "requester"). Used for role-based access control.
    """

    username: str
    disabled: Optional[bool] = None
    role: Optional[str] = None


class UserInDB(UserDetails):
    """
    Model representing a user stored in the database, extending the base UserDetails model.

    Attributes
    ----------
    hashed_password : str
        The hashed password of the user, used for authentication.
    """

    hashed_password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Parameters
    ----------
    plain_password : str
        The plain text password entered by the user.
    hashed_password : str
        The hashed password stored in the database.

    Returns
    -------
    bool
        Returns True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password.

    Parameters
    ----------
    password : str
        The plain text password to hash.

    Returns
    -------
    str
        A hashed version of the given password.
    """
    return pwd_context.hash(password)


def get_user(database_session: Session, username: str) -> Optional[UserInDB]:
    """
    Retrieve user details from the database.

    Parameters
    ----------
    database_session : Session
        The database session.
    username : str
        The username to look up.

    Returns
    -------
    Optional[UserInDB]
        A UserInDB instance if the user exists, None otherwise.
    """
    user = database_session.query(User).filter(User.username == username).first()
    if user:
        return UserInDB(
            username=user.username,
            hashed_password=user.hashed_password,
            disabled=user.disabled,
            role=user.role,
        )
    return None


def authenticate_user(
    database_session: Session, username: str, password: str
) -> Union[UserInDB, bool]:
    """
    Authenticate the user by verifying the password.

    Parameters
    ----------
    database_session : Session
        The database session.
    username : str
        The username of the user.
    password : str
        The password entered by the user.

    Returns
    -------
    Union[UserInDB, bool]
        Returns the authenticated user if successful, otherwise returns False.
    """
    user = get_user(database_session, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Parameters
    ----------
    data : Dict
        Data to encode into the JWT, usually includes user identity.
    expires_delta : Optional[timedelta]
        Optional expiration time for the token. Defaults to 15 minutes.

    Returns
    -------
    str
        The encoded JWT token as a string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(payload=to_encode, key=PRIVATE_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    database_session: Session = Depends(get_database_session),
) -> UserInDB:
    """
    Retrieve the current user from the token.

    Parameters
    ----------
    token : str
        The JWT access token.
    database_session : Session
        The database session.

    Returns
    -------
    UserInDB
        The user associated with the provided token.

    Raises
    ------
    HTTPException
        If the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(jwt=token, key=PUBLIC_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise credentials_exception
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(error)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user(database_session, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserDetails, Depends(get_current_user)]
) -> UserDetails:
    """
    Verify that the current user is active.

    Parameters
    ----------
    current_user : UserDetails
        The current user extracted from the token.

    Returns
    -------
    UserDetails
        The user if they are active.

    Raises
    ------
    HTTPException
        If the user is inactive.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin(
    current_user: Annotated[UserDetails, Depends(get_current_user)]
) -> UserDetails:
    """
    Verify that the current user is an admin.

    Parameters
    ----------
    current_user : UserDetails
        The current user extracted from the token.

    Returns
    -------
    UserDetails
        The user if they have admin permissions.

    Raises
    ------
    HTTPException
        If the user is not an admin.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user


async def get_current_user_or_admin(
    current_user: Annotated[UserDetails, Depends(get_current_user)]
) -> UserDetails:
    """
    Verify that the current user is either a requester or an admin.

    Parameters
    ----------
    current_user : UserDetails
        The current user extracted from the token.

    Returns
    -------
    UserDetails
        The user if they have requester or admin permissions.

    Raises
    ------
    HTTPException
        If the user has insufficient permissions.
    """
    if current_user.role not in ["requester", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user
