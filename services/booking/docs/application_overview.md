## **App Package (`app`)**

<center>

| Sub-Module       | Description                                                                                   |
|------------------|-----------------------------------------------------------------------------------------------|
| **api**          | Contains API endpoint implementations such as submission, acceptance, rejection, deletion, and listing of booking requests. |
| **models**       | Holds the application’s data models for the database (SQLAlchemy ORM) and Pydantic models used for validation and serialization.  |
| **auth.py**      | Implements authentication mechanisms via OAuth2, including password hashing, token creation/validation, and user role management. |
| **config.py**    | Manages the application’s configuration settings, fetching database URLs from AWS Secrets Manager. |
| **db.py**        | Provides database connection and session management using SQLAlchemy. This includes database session creation and dependency injections for FastAPI. |
| **main.py**      | The entry point for the application, configuring the FastAPI instance and routing API endpoints. |

</center>

---

## **Database (`db`)**

<center>

| File                 | Description                                        |
|----------------------|----------------------------------------------------|
| **create_db.sql**    | SQL script for initializing the database schema, used specifically for local development and testing. It sets up the database for a `test-db` service as defined in `db.Dockerfile`. The script is added to the Docker container via `ADD db/create_db.sql /docker-entrypoint-initdb.d` to automatically run upon container initialization. |

</center>

---

## **Docker Files (`docker`)**

<center>

| File                 | Description                                        |
|----------------------|----------------------------------------------------|
| **db.Dockerfile**    | Dockerfile for setting up the test database on container start. |
| **deploy.Dockerfile**| Configures the deployment environment for running the application in ECS.                       |
| **test.Dockerfile**  | Sets up the environment for running tests using `pytest` within a container.                    |

</center>

---

## **Migrations (`migrations`)**

<center>

| File/Folder          | Description                                                                                 |
|----------------------|---------------------------------------------------------------------------------------------|
| **alembic.ini**      | Configuration file for Alembic, handling database migrations.                               |
| **versions**         | Contains versioned migration scripts for schema evolution, ensuring the database remains up-to-date. |

</center>

---

## **Automation Scripts (`scripts`)**

<center>

| Script                   | Description                                                                  |
|--------------------------|------------------------------------------------------------------------------|
| **entrypoint.sh**        | Script executed when the local development and test container starts, initializes application services. |
| **generate_and_store_keys.sh** | Script for generating and storing keys using AWS Secrets Manager.         |
| **run_black_isort.sh**   | Executes linting and formatting commands (`black` and `isort`).              |

</center>

---

## **Tools (`tools`)**

<center>

| Tool                      | Description                                                                                  |
|--------------------------|----------------------------------------------------------------------------------------------|
| **deploy_ecs.py**        | Automates the registration of new task definitions using boto3, executed by the `.github/workflows/ecr_ecs.yml` reusable workflow for both `dev` and `prod` environments. It also launches a standalone container to verify if data migrations need to be run; the `migrations` directory is accessible inside the container. |
| **manage_passwords.py**  | Handles password rotation, securely storing secrets in AWS Secrets Manager and updating the database with new credentials. |
| **manage_passwords_trigger.py** | Orchestrates password rotation by launching a standalone Fargate task that inserts or updates user credentials in the `users` table. |

</center>

---

## **Authentication (`auth.py`)**

<center>

| Functionality               | Description                                                                                               |
|----------------------------|-----------------------------------------------------------------------------------------------------------|
| **Token Creation**         | Creates JWT tokens for user sessions, including role-based and time-based restrictions.                    |
| **Password Hashing**       | Uses `bcrypt` for securely hashing and verifying user passwords.                                           |
| **User Authentication**    | Verifies user credentials against stored values in the database and authenticates users with JWT tokens.   |
| **Role Management**        | Validates user roles (e.g., admin, requester) and enforces access control based on these roles.           |

</center>

---

## **Database Management (`db.py`)**

<center>

| Functionality               | Description                                                                                               |
|----------------------------|-----------------------------------------------------------------------------------------------------------|
| **Session Management**      | Provides SQLAlchemy session creation, ensuring connections are managed efficiently across API requests.   |
| **Dependency Injection**   | Integrates sessions with FastAPI’s dependency system for use in endpoints.                                 |

</center>

---

## **Configuration Management (`config.py`)**

<center>

| Setting/Attribute          | Description                                                                                               |
|----------------------------|-----------------------------------------------------------------------------------------------------------|
| **environment**            | Identifies the environment the application is running in (`dev`, `prod`, or `test`).                       |
| **database_url**           | Fetches the database connection string from AWS Secrets Manager, ensuring secure access.                    |
| **debug/testing flags**    | Controls whether the application runs in debug or testing mode.                                            |

</center>

---

## **API Endpoints (`api`)**

<center>

| Endpoint                 | Description                                                                                                  |
|-------------------------|--------------------------------------------------------------------------------------------------------------|
| **/submit_request**     | Allows submission of new booking requests.                                                                    |
| **/list_requests**      | Lists all booking requests. Restricted to admin users.                                                        |
| **/accept_request**     | Accepts a specific booking request by ID. Restricted to admin users.                                          |
| **/reject_request**     | Rejects a specific booking request by ID. Restricted to admin users.                                          |
| **/delete_request/{id}**| Deletes a booking request by ID. Restricted to admin users.                                                  |
| **/ping/**              | Health check endpoint that verifies database migration status. Ensures the system is up-to-date before deployment. |

</center>

---

## **SQLAlchemy ORM & Pydantic Models**

### **Database Models (`models/db_models.py`)**

<center>

| Model             | Description                                                                                   |
|-------------------|-----------------------------------------------------------------------------------------------|
| **User**          | Represents users, storing their username, hashed password, role, and status (active/disabled).|
| **Booking**       | Represents a booking request, storing event details, duration, status, and requestor email.  |

</center>

### **Pydantic Models (`models/pydantic_models.py`)**

<center>

| Model               | Description                                                                                  |
|---------------------|----------------------------------------------------------------------------------------------|
| **Address**         | Represents event addresses, including validation for street, city, state, and country fields.|
| **RequestStatus**   | Enum for status values: `pending`, `accepted`, `rejected`.                                    |
| **BookingResponse** | Pydantic model representing booking details, including validation for event time, topic, and address.|
| **SubmissionRequest** | Model for incoming booking submissions, used for validation in API endpoints.              |

</center>
