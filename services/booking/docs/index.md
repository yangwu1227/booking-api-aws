# Booking Service API

An asynchronous RESTful API built with Python, FastAPI, and Docker for learning purposes. The application enables users to submit talk booking requests and provides speakers with endpoints to manage these requests via the API. It integrates with a PostgreSQL database hosted on AWS RDS and is containerized using Docker for both local development and deployment on AWS ECS Fargate.

The API includes the following features:

- **Submit booking requests:** Users can submit requests for talks.
- **Retrieve booking requests:** Speakers can view all submitted booking requests.
- **Update booking requests by ID:** Speakers can accept or reject booking requests based on their ID.
- **Delete booking requests by ID:** Speakers can remove booking requests using their ID.
