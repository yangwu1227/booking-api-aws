## OAuth2 

The booking service API uses [**OAuth2**](https://auth0.com/intro-to-iam/what-is-oauth-2) as its authentication mechanism, providing a secure way for access control. The diagram below illustrates the flow of the OAuth2 authentication mechanism, showing how the client application interacts with the authorization and resource endpoints to authenticate and access protected resources.

<p align="center">
    <img src="../diagrams/token_based_authorization.png" width="100%" alt="OAuth2 Authentication Flow Diagram">
</p>
<p align="center">
    <em>Diagram: Flow of OAuth2 authentication</em>
</p>

### OAuth2 Flow in the Booking Service API

### Requesting a Token

The `/token` endpoint handles login, where the user sends credentials using the `OAuth2PasswordRequestForm`. When valid credentials are provided, a JWT token is generated.

```python
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm, database_session: Session = Depends(get_database_session)) -> Token:
    user = authenticate_user(database_session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")
```

The form data is sent as:

```plaintext
Content-Type: application/x-www-form-urlencoded
username=your_username&password=your_password
```

The `Token` model represents the JWT token returned after successful authentication:

```python
class Token(BaseModel):
    access_token: str
    token_type: str
```

The `authenticate_user` function verifies the user’s identity by retrieving their details from the database using `get_user` and validating the password with `verify_password`.

```python
def authenticate_user(database_session: Session, username: str, password: str) -> Union[UserInDB, bool]:
    user = get_user(database_session, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
```

The `create_access_token` function then generates the JWT token using the provided user information.

```python
def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(payload=to_encode, key=PRIVATE_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

A JWT is an encoded string containing user information and an expiration time, signed using the digital signatures and the specified algorithm. A JWT is composed of three parts separated by dots. For example:

```plaintext
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

- **Header**: Encodes metadata such as the signing algorithm (`eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`).
- **Payload**: Contains claims like user ID and expiration time (`eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ`).
- **Signature**: A hashed combination of the header, payload, and the secret key (`SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c`).

### Retrieving User Credentials from the Database

The `get_user` function accesses the database to retrieve the user record, which is then wrapped in a `UserInDB` model if the user exists.

```python
def get_user(database_session: Session, username: str) -> Optional[UserInDB]:
    user = database_session.query(User).filter(User.username == username).first()
    if user:
        return UserInDB(username=user.username, hashed_password=user.hashed_password, disabled=user.disabled, role=user.role)
    return None
```

The `UserInDB` model represents the user’s details, including the username, hashed password, and role.

```python
class UserDetails(BaseModel):
    username: str
    disabled: Optional[bool] = None
    role: Optional[str] = None

class UserInDB(UserDetails):
    hashed_password: str
```

The separation of `UserDetails` and `UserInDB` models distinguishes between the user details stored in the database (`UserInDB`) and the user details returned to the client (`UserDetails`), ensuring the hashed password remains secure.

### Validating the Password

The `verify_password` function compares the plain text password provided during login to the hashed password stored in the database.

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

This function uses the [CryptContext](https://passlib.readthedocs.io/en/stable/lib/passlib.context.html#passlib.context.CryptContext) class from `passlib` to validate the password securely.

### Retrieving and Validating the Current User

The `get_current_user` function decodes the JWT token via `jwt.decode` to extract the user’s information (e.g., `username`). It validates the token's integrity and checks for expiration.

```python
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], database_session: Session = Depends(get_database_session)) -> UserInDB:
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
```

The `sub` key in the payload contains the username, which is used to retrieve the user from the database. If the user is not found, an unauthorized error is raised.

#### OAuth2PasswordBearer 

The `oauth2_scheme` dependable is an instance of `OAuth2PasswordBearer`, a dependency provided by FastAPI for OAuth2 authentication. It is used to extract the Bearer token from the request's `Authorization` header.

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

- The parameter `tokenUrl="token"` specifies the endpoint where the token can be obtained. In this case, the `/token` endpoint issues the JWT when a user provides valid credentials.
- When used in `Depends(oauth2_scheme)`, FastAPI automatically extracts and validates the token passed in the request. The token is then passed to the `get_current_user` function as a dependency.

The `oauth2_scheme` ensures that each request to protected endpoints must include a valid token in the `Authorization` header (e.g., `Authorization: Bearer <token>`). Without a valid token, access to the endpoint will be denied, and an HTTP 401 Unauthorized error will be returned.

An example of a request to a protected endpoint including the token:

```bash
curl -X 'POST' \
  'https://api.example.com/booking/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <access_token_placeholder>' \
  -H 'Content-Type: application/json' \
  -d '{
    ...
  }'
```

The token, once extracted, is validated and decoded within `get_current_user` to authenticate the user and retrieve user details from the database.

#### TokenData Model

The `TokenData` model represents the token data, which includes the username:

```python
class TokenData(BaseModel):
    username: str
```

### Verifying User Activity and Role

- `get_current_active_user` ensures the user is active.
- `get_current_admin` verifies if the user has an admin role.
- `get_current_user_or_admin` checks if the user has either "admin" or "requester" roles.

```python
async def get_current_active_user(current_user: Annotated[UserDetails, Depends(get_current_user)]) -> UserDetails:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

```python
async def get_current_admin(current_user: Annotated[UserDetails, Depends(get_current_user)]) -> UserDetails:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user
```

```python
async def get_current_user_or_admin(current_user: Annotated[UserDetails, Depends(get_current_user)]) -> UserDetails:
    if current_user.role not in ["requester", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user
```

These functions use `get_current_user` as a dependency to validate the token and additionally check for specific conditions (e.g., if the user is active or has the required permissions).

### Accessing Protected Resources

For protected endpoints like `GET`, `POST`, and `DELETE`, these dependencies verify the user’s identity and role before allowing access to the resource.

```python
@router.post(
    "/",
    status_code=201,
    response_model=BookingResponse,
    dependencies=[Depends(get_current_user_or_admin), Depends(get_current_active_user)],
)

@router.get(
    "/",
    status_code=200,
    response_model=BookingResponseList,
    dependencies=[Depends(get_current_admin), Depends(get_current_active_user)],
)

@router.post(
    "/accept/",
    status_code=200,
    response_model=BookingResponse,
    dependencies=[Depends(get_current_admin), Depends(get_current_active_user)],
)

@router.post(
    "/reject/",
    status_code=200,
    response_model=BookingResponse,
    dependencies=[Depends(get_current_admin), Depends(get_current_active_user)],
)

@router.delete(
    "/{id}/",
    status_code=200,
    response_model=BookingResponse,
    dependencies=[Depends(get_current_admin), Depends(get_current_active_user)],
)
```

---

## Digital Signature Algorithms in the Booking Service API

The booking service API uses EdDSA (Edwards-curve Digital Signature Algorithm) for signing and verifying JWT tokens. This algorithm uses the Ed25519 curve, which offers 128-bit security.

#### Asymmetric (Public-Key) Cryptography

Asymmetric cryptography involves a pair of keys: a **private key** used for signing (encoding) and a **public key** used for verifying (decoding).

- **`Ed25519`**: This is the algorithm used for signing and verifying tokens. 
- The **private key** is securely stored in AWS Secrets Manager and used in `create_access_token` to sign tokens.
- The **public key** is also stored in AWS Secrets Manager and is used in `get_current_user` to verify the authenticity of tokens.

### Code Implementation Highlights

#### Setting Up the Environment and Keys

```python
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
```

The `PUBLIC_KEY` and `PRIVATE_KEY` are fetched from AWS Secrets Manager in `dev` and `prod` environments. In `test` mode, the keys are set to dummy values for testing purposes. This is because integration tests involving protected endpoints use mocked versions of the authentication functions; therefore, no real keys are needed.

#### Signing and Verifying Tokens

- **Signing** (using the private key):

    ```python
    encoded_jwt = jwt.encode(payload=to_encode, key=PRIVATE_KEY, algorithm=ALGORITHM)
    ```

- **Verifying** (using the public key):

    ```python
    payload = jwt.decode(jwt=token, key=PUBLIC_KEY, algorithms=[ALGORITHM])
    ```

Both operations use `EdDSA` with the Ed25519 curve to ensure secure signing and verification.

### Generating and Storing Ed25519 Keys (Relevant Script Lines)

The `scripts/generate_and_store_keys.sh` script generates Ed25519 keys, encodes them in base64, and stores them in AWS Secrets Manager. The secrets resources are provisioned in the `infrastructure/modules/booking_service/api_keys_creds.tf` Terraform configurtation file.

1. **Generating Keys**:

    ```bash
    openssl genpkey -algorithm Ed25519 -out "$PRIVATE_KEY_FILE"
    openssl pkey -in "$PRIVATE_KEY_FILE" -pubout -out "$PUBLIC_KEY_FILE"
    ```

2. **Base64 Encoding**:

    ```bash
    PRIVATE_KEY=$(base64 < "$PRIVATE_KEY_FILE")
    PUBLIC_KEY=$(base64 < "$PUBLIC_KEY_FILE")
    ```

3. **Storing in AWS Secrets Manager**:

    ```bash
    aws secretsmanager put-secret-value --secret-id "private_key_${ENV}" --secret-string "$PRIVATE_KEY" --profile "$AWS_PROFILE"
    aws secretsmanager put-secret-value --secret-id "public_key_${ENV}" --secret-string "$PUBLIC_KEY" --profile "$AWS_PROFILE"
    ```

These lines generate, encode, and store Ed25519 keys in AWS Secrets Manager so they can be securely accessed by the booking service API at runtime.
