from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import Token, authenticate_user, create_access_token
from app.db import get_database_session

ACCESS_TOKEN_EXPIRE_MINUTES = 30
router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    database_session: Session = Depends(get_database_session),
) -> Token:
    """
    Handles user login and returns a JWT token for valid credentials.

    Parameters
    ----------
    form_data : OAuth2PasswordRequestForm
        The form data submitted for authentication, including username and password.
    database_session : Session
        The SQLAlchemy database session for accessing user records.

    Returns
    -------
    Token
        The JWT token and token type if authentication is successful.

    Raises
    ------
    HTTPException
        If the authentication fails due to incorrect username or password.
    """
    # Authenticate the user using the database session
    user = authenticate_user(database_session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires  # type: ignore[union-attr]
    )
    # Return the generated token and token type
    return Token(access_token=access_token, token_type="bearer")
