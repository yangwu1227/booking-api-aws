## **App Package (`app`)**

<center>

| Sub-Module       | Description                                                                                   |
|------------------|-----------------------------------------------------------------------------------------------|
| **api**          | Contains API endpoint implementations such as submission, acceptance, rejection, and listing of requests.  |
| **models**       | Holds the application’s data models, both for database (SQLAlchemy) and Pydantic models used for validation and serialization.  |
| **auth.py**      | Implements authentication mechanisms, including password hashing, token creation/validation, and user role management. |
| **config.py**    | Manages the application’s configuration settings, fetching values like database URLs and environment details from AWS Secrets Manager. |
| **db.py**        | Provides database connection and session management using SQLAlchemy. This includes session creation and dependency injections for FastAPI. |
| **main.py**      | The entry point for the application, configuring the FastAPI instance and routing API endpoints. |

</center>

## **Database (`db`)**

<center>

| File                 | Description                                        |
|----------------------|----------------------------------------------------|
| **create_db.sql**    | SQL script for initializing the database schema.   |

</center>

## **Docker Configuration (`docker`)**

<center>

| File                 | Description                                        |
|----------------------|----------------------------------------------------|
| **db.Dockerfile**    | Dockerfile for setting up the database environment. |
| **deploy.Dockerfile**| Configures the deployment environment for running the application in ECS.                       |
| **test.Dockerfile**  | Sets up the environment for running tests using `pytest` within a container.                    |

</center>

## **Migrations (`migrations`)**

<center>

| File/Folder          | Description                                                                                 |
|----------------------|---------------------------------------------------------------------------------------------|
| **alembic.ini**      | Configuration file for Alembic, handling database migrations.                               |
| **versions**         | Contains versioned migration scripts for schema evolution, ensuring the database remains up-to-date. |

</center>

## **Scripts (`scripts`)**

<center>

| Script                   | Description                                                                  |
|--------------------------|------------------------------------------------------------------------------|
| **entrypoint.sh**        | Script executed when the container starts, initializes application services. |
| **generate_and_store_keys.sh** | Script for generating and storing keys using AWS Secrets Manager.         |
| **run_black_isort.sh**   | Executes linting and formatting commands (`black` and `isort`).              |

</center>

## **Tools (`tools`)**

<center>

| Tool                      | Description                                                                                  |
|--------------------------|----------------------------------------------------------------------------------------------|
| **deploy_ecs.py**        | Automates the deployment of ECS services using boto3 and ECS APIs.                           |
| **manage_passwords.py**  | Manages password rotation, storing secrets in AWS Secrets Manager and updating the database. |
| **manage_passwords_trigger.py** | Orchestrates password rotation by launching ECS tasks with specified configurations.   |

</center>

## **Authentication (`auth.py`)**

<center>

| Functionality               | Description                                                                                               |
|----------------------------|-----------------------------------------------------------------------------------------------------------|
| **Token Creation**         | Creates JWT tokens for user sessions, including role-based and time-based restrictions.                    |
| **Password Hashing**       | Uses `bcrypt` for securely hashing and verifying user passwords.                                           |
| **User Authentication**    | Verifies user credentials against stored values in the database and authenticates users with JWT tokens.   |
| **Role Management**        | Validates user roles (e.g., admin, requester) and enforces access control based on these roles.           |

</center>

## **Database Management (`db.py`)**

<center>

| Functionality               | Description                                                                                               |
|----------------------------|-----------------------------------------------------------------------------------------------------------|
| **Session Management**      | Provides SQLAlchemy session creation, ensuring connections are managed efficiently across API requests.   |
| **Dependency Injection**   | Integrates sessions with FastAPI’s dependency system for use in endpoints.                                 |

</center>

## **Configuration Management (`config.py`)**

<center>

| Setting/Attribute          | Description                                                                                               |
|----------------------------|-----------------------------------------------------------------------------------------------------------|
| **environment**            | Identifies the environment the application is running in (`dev`, `prod`, or `test`).                       |
| **database_url**           | Fetches the database connection string from AWS Secrets Manager, ensuring secure access.                    |
| **debug/testing flags**    | Controls whether the application runs in debug or testing mode.                                            |

</center>

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

## **Models**

### **Database Models (`models/db_models.py`)**

<center>

| Model             | Description                                                                                   |
|-------------------|-----------------------------------------------------------------------------------------------|
| **User**          | Represents users, storing their username, hashed password, role, and status (active/disabled).|
| **Booking**       | Represents a booking request, storing event details, duration, status, and requestor information.  |

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

## **Tools and Management Scripts (`tools`)**

<center>

| Tool                      | Description                                                                                  |
|--------------------------|----------------------------------------------------------------------------------------------|
| **deploy_ecs.py**        | Automates registering new task definitions and migrations with ECS services.                 |
| **manage_passwords.py**  | Rotates user passwords, updates AWS Secrets Manager, and syncs with the database securely.   |
| **manage_passwords_trigger.py** | Launches standalone ECS tasks for password rotation with specific parameters based on environment.|

</center>
