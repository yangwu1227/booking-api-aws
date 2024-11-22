# FastAPI Booking Service API 

An asynchronous RESTful API built with Python, FastAPI, and Docker for learning purposes. It allows users to create, retrieve, update, and delete booking requests. The app integrates with a PostgreSQL database hosted on AWS RDS and is containerized using Docker for both local development and deployment on AWS ECS Fargate.

[**Project Documentation**](https://yangwu1227.github.io/booking-service-api/)

## Infrastructure

- **AWS ECS Fargate**: Containerized application for deployment.
- **FastAPI**: Provides asynchronous API endpoints.
- **AWS RDS (PostgreSQL)**: Used as the database for storing booking requests.
- **SQLAlchemy & Alembic**: ORM and migration tool for database management.
- **GitHub Actions CI**: Automated testing, Docker builds, and pushing images to Amazon ECR.
- **AWS VPC**: Provides network isolation and security for the services.
- **Terraform**: Manages infrastructure as code, defining ECS, RDS, IAM, and networking configurations.

## Role-Based Access

- **Admin**: Has access to all API endpoints.
- **Requester**: Can only access the `/booking/` endpoint to submit a booking request.

## Authentication

Before making any API requests, authenticate to receive a Bearer token. The password should be URL-encoded using `urllib.parse.quote(password)` in Python or an online encoder.

### `curl` Example

First, export the URL-encoded password:

```bash 
PASSWORD='<password_placeholder>'
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${PASSWORD}'))")
```

Then:

```bash
curl -X 'POST' \
  'https://<domain_placeholder>/token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "grant_type=password&username=requester&password=${ENCODED_PASSWORD}&scope=&client_id=string&client_secret=string"
```

### Python `requests` Example

```python
import requests
import urllib.parse

url = "https://<domain_placeholder>/token"
username = "requester"
password = urllib.parse.quote("<password_placeholder>")
data = {
    "grant_type": "password",
    "username": username,
    "password": password,
    "scope": "",
    "client_id": "string",
    "client_secret": "string"
}

response = requests.post(url, data=data, headers={
    "accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded"
})

print(response.json())
```

## API Requests

### 1. Submit a Booking Request (`POST /booking/`)

#### `curl` Example

```bash
curl -X 'POST' \
  'https://<domain_placeholder>/booking/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <access_token_placeholder>' \
  -H 'Content-Type: application/json' \
  -d '{
    "event_time": "2024-10-06T21:19:49.243Z",
    "address": {
      "street": "string",
      "city": "string",
      "state": "string",
      "country": "China"
    },
    "topic": "string",
    "duration_minutes": 1,
    "requested_by": "requester@example.com"
  }'
```

#### Python `requests` Example

```python
import requests

url = "https://<domain_placeholder>/booking/"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer <access_token_placeholder>",
    "Content-Type": "application/json"
}
data = {
    "event_time": "2024-10-06T21:19:49.243Z",
    "address": {
        "street": "string",
        "city": "string",
        "state": "string",
        "country": "China"
    },
    "topic": "string",
    "duration_minutes": 1,
    "requested_by": "requester@example.com"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### 2. Accept a Booking (`POST /booking/accept/`)

#### `curl` Example

```bash
curl -X 'POST' \
  'https://<domain_placeholder>/booking/accept/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <access_token_placeholder>' \
  -H 'Content-Type: application/json' \
  -d '{"id": <id_placeholder>}'
```

#### Python `requests` Example

```python
import requests

url = "https://<domain_placeholder>/booking/accept/"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer <access_token_placeholder>",
    "Content-Type": "application/json"
}
data = {"id": <id_placeholder>}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### 3. Reject a Booking (`POST /booking/reject/`)

#### `curl` Example

```bash
curl -X 'POST' \
  'https://<domain_placeholder>/booking/reject/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <access_token_placeholder>' \
  -H 'Content-Type: application/json' \
  -d '{"id": <id_placeholder>}'
```

#### Python `requests` Example

```python
import requests

url = "https://<domain_placeholder>/booking/reject/"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer <access_token_placeholder>",
    "Content-Type": "application/json"
}
data = {"id": <id_placeholder>}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### 4. Delete a Booking (`DELETE /booking/{id}/`)

#### `curl` Example

```bash
curl -X 'DELETE' \
  'https://<domain_placeholder>/booking/<id_placeholder>/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <access_token_placeholder>'
```

#### Python `requests` Example

```python
import requests

url = "https://<domain_placeholder>/booking/"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer <access_token_placeholder>"
}

response = requests.get(url, headers=headers)
print(response.json())
```

### 5. Get All Bookings (`GET /booking/`)

#### `curl` Example

```bash
curl -X 'GET' \
  'https://<domain_placeholder>/booking/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <access_token_placeholder>'
```

#### Python `requests` Example

```python
import requests

url = "https://<domain_placeholder>/booking/"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer <access_token_placeholder>"
}

response = requests.get(url, headers=headers)
print(response.json())
```

### Notes

- `<access_token_placeholder>` should be replaced with the actual token obtained from the authentication step.
- `<domain_placeholder>` should be replaced with the actual domain name.
- `<password_placeholder>` should be replaced with the actual password stored in the `users` table in the database.
