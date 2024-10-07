# Set Up Workflows

## Environment Setup

### Install PDM

The dependency manager used in this project is [pdm](https://github.com/pdm-project/pdm). To install it, run the following command:

```bash
$ curl -sSL https://pdm-project.org/install-pdm.py | python3 -
```

Or, alternatively, other [installation methods](https://pdm-project.org/en/latest/#installation) can be used.

### Install Dependencies

The dependencies are broken into groups:

* Default dependencies: required for the core functionality of the project in production.

* Development dependencies: required for development, testing, and documentation.

The specified python version in `pyproject.toml` is `>=3.11`, and so a **python 3.11** interpreter should be used. 

#### Conda

To do so with [conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html):

```bash
$ conda search python | grep " 3\.\(10\|11\|12\)\."
$ yes | conda create --name booking_service_api python=3.11.9
$ conda activate booking_service_api
$ pdm use -f $(which python3)
$ pdm install
```

#### Vitualenv

To do so with [virtualenv](https://github.com/pypa/virtualenv), use the [pdm venv](https://pdm-project.org/en/latest/reference/cli/#venv) command:

```bash 
$ pdm venv create --name booking_service_api --with virtualenv 3.11.9 
# To activate the virtual environment
$ eval $(pdm venv activate booking_service_api) 
$ pdm install
```

---

## Docker Compose for Local Development

[Docker Compose](https://docs.docker.com/compose/) is used for local development to isolate the application and its dependencies in a containerized environment. Two services are defined the the `compose.yml` file:

* `test`: The service for running the application, unit, integration, and end-to-end tests. The following directories are mapped or [bind-mounted](https://docs.docker.com/engine/storage/bind-mounts/) from the host to the container:

  - `app/**`: The application code to run the FastAPI application.
  - `tests/**`: The test code as all tests are run in the container.
  - `pyproject.toml`: The project configuration file, which includes the dependencies, pytest configurations, and other project settings.
  - `migrations`: The Alembic migrations directory to manage the database schema. This is mounted to the container to apply migrations each time a new container is created (i.e., `docker compose up --detach --build`).

* `db-test`: The service for running the PostgreSQL database for testing purposes. The database is initialized with the schema and data required for testing based on the migration files in the `migrations` directory.

### Build & Run

To build the images and run the containers in the background:

```bash
$ docker compose up --detach --build
```

This setup allows for automatic reloading of the application when changes are made to the code during development. The application is available at [http://localhost:8004](http://localhost:8004) or whichever port is specified in the `compose.yml` file.

To stop the containers without removing them:

```bash
$ docker compose stop
```

To stop, remove the containers, and remove named volumes:

```bash
$ docker compose down --volumes
```

To view the logs of the services:

```bash
$ docker compose logs <service-name>
```

To run an interactive shell in a service container:

```bash
# Or /bin/bash
$ docker compose exec <service-name> /bin/sh
```

### Testing with Pytest

The test suite is run using [pytest](https://docs.pytest.org/en/stable/). The integration tests are run against a PostgreSQL database running in a Docker container. The `DATABASE_URL_TEST` database connection string is set as an environment variable in the `compose.yml` file.

<center>

| Test Type          | Description                                                                                   |
|--------------------|-----------------------------------------------------------------------------------------------|
| **Unit Tests**     | Validates individual components like models, services, and utility functions.                 |
| **Integration Tests** | Tests the integration between database services and API endpoints.                          |
| **End-to-End Tests**  | Simulates real user flows, ensuring the entire application functions as expected.           |

</center>

```bash
$ docker compose exec <service-name> python3 -m pytest -s tests/integration tests/unit tests/end_to_end -v
```

## Automation 

### Formatting with Black and Isort

The `scripts` directory contains a `run_black_isort.sh` shell script that runs [black](https://black.readthedocs.io/en/stable/) and [isort](https://pycqa.github.io/isort/) on the project files. The script is also used in the GitHub Actions workflows to ensure consistent code formatting. 

Run the script as follows:

```bash
$ cd services/booking
$ scripts/run_black_isort.sh
```

