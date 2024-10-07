## Directory Structure

```
.
├── README
├── alembic.ini
├── env.py
├── script.py.mako
└── versions
    ├── 00ba29ba9ef0_create_user_table.py
    └── be5c4de9546c_initial_migration.py
```

- **alembic.ini**: The main Alembic configuration file where settings, including the database URL and migration paths, are defined.
- **env.py**: The script Alembic uses to set up the migration environment, configuring the database connection and autogenerate support for models.
- **script.py.mako**: A template file used for generating migration scripts.
- **versions/**: Directory containing versioned migration scripts. Each migration script tracks specific changes to the database schema.

## Alembic Configuration (`alembic.ini`)

The `alembic.ini` file configures how Alembic connects to the database and how migration scripts are generated. This file can exist in any directory, with the location to it specified by either the `--config` option for the `alembic` runner or the `ALEMBIC_CONFIG` environment variable. Key settings include:

| Setting                   | Description                                                                                             |
|--------------------------|---------------------------------------------------------------------------------------------------------|
| `script_location`        | Points to the directory where migration scripts are stored (`migrations/versions`).                      |
| `sqlalchemy.url`         | Defines the database connection string, used when running migrations (`driver://user:pass@localhost/dbname`). This can be overridden dynamically in `env.py` using `get_settings()`. |
| `version_path_separator` | Determines the separator used for multiple version paths (default is based on the operating system).      |
| `[loggers]`, `[handlers]`, `[formatters]` | Logging configuration for Alembic, enabling detailed logs during migration operations. |

## Environment Setup (`env.py`)

The `env.py` is the core of Alembic’s migration environment, setting up connections and managing how migrations are applied. It handles two scenarios: offline and online migration modes.

#### Key Sections:

1. **Configuration Setup**:

    - The configuration object (`config`) reads values from `alembic.ini`.
    - Logging configuration is set up using `fileConfig(config.config_file_name)`.

2. **Target Metadata**:
   
    - `target_metadata` is assigned the metadata from SQLAlchemy models (`Base.metadata`), enabling autogeneration of migrations based on ORM models.
   
    ```python
    from app.models.db_models import Base
    target_metadata = [Base.metadata]
    ```

3. **Offline Migrations (`run_migrations_offline`)**:

    - Runs migrations without an active database connection. Suitable for generating SQL scripts.
    - Uses `context.execute()` to emit SQL directly.
   
    ```python
    def run_migrations_offline() -> None:
        url = config.get_main_option("sqlalchemy.url", get_settings().database_url)
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        with context.begin_transaction():
            context.run_migrations()
    ```

4. **Online Migrations (`run_migrations_online`)**:
   
    - Creates an SQLAlchemy engine and associates it with the migration context.
    - It fetches the database URL dynamically from the application’s settings using `get_settings()` to ensure the environment is correctly set (`dev`, `test`, `prod`).

    ```python
    def run_migrations_online() -> None:
        alembic_config = config.get_section(config.config_ini_section, {})
        alembic_config["sqlalchemy.url"] = get_settings().database_url
        connectable = engine_from_config(
            alembic_config,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    ```

## SQLAlchemy Models and Migrations

The database models are defined using SQLAlchemy ORM, which maps Python classes to database tables. Alembic detects changes to these models for migration generation.

#### Example Models:

```python
class User(Base):
    __tablename__ = "users"
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    username = mapped_column(String(100), unique=True, nullable=False)
    hashed_password = mapped_column(String, nullable=False)
    disabled = mapped_column(Boolean, default=False)
    role = mapped_column(String(50), nullable=False)
```

Alembic uses the `Base.metadata` to detect changes when generating migrations. Whenever a model is added or modified, a new migration script can be generated.

## Dependencies and Configuration (`db.py` and `config.py`)

- **`db.py`**: This module provides the connection and session management using SQLAlchemy. It utilizes the application’s settings to dynamically set up database connections.
  
  ```python
  def get_local_session() -> sessionmaker:
      settings = get_settings()
      database_url = settings.database_url
      engine = create_engine(database_url)
      return sessionmaker(bind=engine)
  ```

- **`config.py`**: Configuration management module using Pydantic for structured settings. It dynamically fetches database connection strings from AWS Secrets Manager, ensuring that environment-specific configurations are correctly applied.

  ```python
  class BaseAppSettings(BaseSettings):
      environment: str
      _database_url: Optional[str] = None
      
      @property
      def database_url(self) -> str:
          if self._database_url is None:
              sm = boto3.client("secretsmanager")
              self._database_url = sm.get_secret_value(SecretId=f"db_connection_string_{self.environment}")["SecretString"]
          return self._database_url
  ```

  This dynamic setup allows `env.py` to fetch the correct database URL based on the environment, ensuring consistent configurations during migrations.

## Migration Scripts (`versions` Directory)

Each migration script captures specific changes made to the database schema:

- **Naming**: The script name starts with a revision ID (e.g., `00ba29ba9ef0`) and includes a slug for clarity (`create_user_table`).

- **Structure**:

    - **`upgrade` function**: Contains SQL statements or ORM-based changes to upgrade the schema.
    - **`downgrade` function**: Reverses changes made by `upgrade`, allowing rollback of migrations.

    ```python
    def upgrade() -> None:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=100), nullable=False),
            sa.Column('hashed_password', sa.String(), nullable=False),
            sa.Column('disabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('role', sa.String(length=50), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
    ```

## Useful Commands

- **Initialize Alembic (First Time)**:

  ```bash
  $ docker compose exec <service-name> alembic -c migrations/alembic.ini init migrations
  ```

- **Generate Migration**:

  ```bash
  $ docker compose exec <service-name> alembic -c migrations/alembic.ini revision --autogenerate -m "describe change"
  ```

- **Apply Migration**:

  ```bash
  $ docker compose exec <service-name> alembic -c migrations/alembic.ini upgrade head
  ```

- **Rollback Migration**:

  ```bash
  $ docker compose exec <service-name> alembic -c migrations/alembic.ini downgrade -1
  ```

## SQLAlchemy Dialect and Driver Compatibility

Ensure the correct driver matches the database connection string. In this project, the **psycopg3** driver is used with the connection string:

```python
postgresql+psycopg://user:password@host:port/dbname
```

**psycopg** (version 3) is a new driver compatible with PostgreSQL, and it has both synchronous and asynchronous dialects:

- **Synchronous (Used in this Project)**:

    ```python
    from sqlalchemy import create_engine
    sync_engine = create_engine("postgresql+psycopg://user:password@localhost/dbname")
    ```

- **Asynchronous**:

    ```python
    from sqlalchemy.ext.asyncio import create_async_engine
    asyncio_engine = create_async_engine("postgresql+psycopg://user:password@localhost/dbname")
    ```

Refer to the SQLAlchemy documentation for more information on using psycopg with SQLAlchemy: [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg).
