import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.auth import (
    UserInDB,
    get_current_active_user,
    get_current_admin,
    get_current_user_or_admin,
)
from app.db import get_database_session
from app.main import app
from app.models import *


def mock_get_current_user_or_admin() -> UserInDB:
    """
    Mock function to return a UserInDB instance for the admin.

    Returns
    -------
    UserInDB
        A UserInDB instance for the admin user.
    """
    return UserInDB(
        username="admin",
        full_name="Admin User",
        email="admin@example.com",
        hashed_password="$2b$12$hashed_password",  # Mock hashed password
        role="admin",
        disabled=False,
    )


def mock_get_current_admin() -> UserInDB:
    """
    Mock function to return a UserInDB instance for the admin.

    Returns
    -------
    UserInDB
        A UserInDB instance for the admin user.
    """
    return mock_get_current_user_or_admin()


def mock_get_current_active_user() -> UserInDB:
    """
    Mock function to return a UserInDB instance for an active user.

    Returns
    -------
    UserInDB
        A UserInDB instance for an active user.
    """
    return mock_get_current_user_or_admin()


@pytest.fixture(scope="class")
def client(database_session: Session) -> TestClient:
    """
    Fixture test client that allows for request to be made against the ASGI application.

    Parameters
    ----------
    database_session : Session
        SQLAlchemy session to interact with the test database.
    """
    # Override authentication dependencies to bypass access control
    app.dependency_overrides[get_current_user_or_admin] = mock_get_current_user_or_admin
    app.dependency_overrides[get_current_admin] = mock_get_current_admin
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    # Mock database session
    app.dependency_overrides[get_database_session] = lambda: database_session
    return TestClient(app)


class TestBookingAPI(object):
    """
    Test class for all booking-related API endpoints.
    """

    def test_health_check(self, client: TestClient) -> None:
        """
        Test for the health check endpoint.
        """
        response = client.get("/ping/")
        assert response.status_code == 200
        assert response.json() == {"message": "ok"}

    def test_submit_request(self, client: TestClient, database_session: Session) -> None:
        """
        Test for the submit request endpoint.

        - Given a request data from a client.
        - When the client submits the request.
        - Then the response should be a BookingResponse instance with the same data and a status of "pending". The ID should be auto-generated and is not a part of the request data nor the response data.
        """
        request_data = {
            "event_time": "2024-10-03T05:07:54.259000Z",
            "address": {
                "street": "123 Main St",
                "city": "Springfield",
                "state": "IL",
                "country": "United States",
            },
            "topic": "Test Topic",
            "duration_minutes": 30,
            "requested_by": "test@gmail.com",
        }
        response = client.post("/booking/", json=request_data)
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["event_time"] == request_data["event_time"]
        assert response_data["address"] == request_data["address"]
        assert response_data["topic"] == request_data["topic"]
        assert response_data["duration_minutes"] == request_data["duration_minutes"]
        assert response_data["requested_by"] == request_data["requested_by"]
        assert response_data["status"] == "pending"

    def test_list_requests(self, client: TestClient, database_session: Session) -> None:
        """
        Test for the list requests endpoint.

        - Given existing requests in the database.
        - When the client sends a request to list all requests.
        - Then the response should be a BookingResponseList instance with a list of BookingResponse instances, each containing the same data as the original request data and a status of "pending". The
        ID should be a part of the response data since the database is queried.
        """
        # Submit a request
        request_data = {
            "event_time": "2024-10-03T05:07:54.259000",
            "address": {
                "street": "123 Main St",
                "city": "Seoul",
                "state": None,
                "country": "Korea, Democratic People's Republic of",
            },
            "topic": "Statistics",
            "duration_minutes": 45,
            "requested_by": "test@yahoo.com",
        }
        client.post("/booking/", json=request_data)
        # List all requests
        response = client.get("/booking/")
        assert response.status_code == 200
        # The response is a BookingResponseList, whose attribute "bookings" is a list of BookingResponse objects
        response_data = response.json().get("bookings")
        assert isinstance(response_data, list)
        new_record = response_data[-1]
        assert new_record["event_time"] == request_data["event_time"]
        assert new_record["address"] == request_data["address"]
        assert new_record["topic"] == request_data["topic"]
        assert new_record["duration_minutes"] == request_data["duration_minutes"]
        assert new_record["requested_by"] == request_data["requested_by"]
        assert new_record["status"] == "pending"

    def test_accept_request(self, client: TestClient, database_session: Session) -> None:
        """
        Test for the accept request endpoint.

        - Given an existing request in the database.
        - When the client (speaker) wishes to accept a specific request.
        - Then the response should be an updated BookingResponse instance with the status set to "accepted".
        """
        # Submit a request using the submit request endpoint
        request_data = {
            "event_time": "2024-10-03T05:07:54.259000",
            "address": {
                "street": "123 Main St",
                "city": "Tokyo",
                "state": None,
                "country": "Japan",
            },
            "topic": "Statistics",
            "duration_minutes": 25,
            "requested_by": "test@outlook.com",
        }
        client.post("/booking/", json=request_data)
        # Get the latest request using the list requests endpoint
        response_get = client.get("/booking/")
        response_data_get = response_get.json().get("bookings")
        new_record = response_data_get[-1]
        # Accept the request, using the accept request endpoint; the response should be an updated BookingResponse instance
        response_accept = client.post("/booking/accept", json={"id": new_record["id"]})
        assert response_accept.status_code == 200
        response_data_accept = response_accept.json()
        assert response_data_accept["id"] == new_record["id"]
        assert response_data_accept["status"] == "accepted"

    def test_reject_request(self, client: TestClient, database_session: Session) -> None:
        """
        Test for the reject request endpoint.

        - Given an existing request in the database.
        - When the client (speaker) wishes to reject a specific request.
        - Then the response should be an updated BookingResponse instance with the status set to "rejected".
        """
        # Submit a request using the submit request endpoint
        request_data = {
            "event_time": "2024-10-03T05:07:54.259000",
            "address": {
                "street": "123 Main St",
                "city": "Paris",
                "state": None,
                "country": "France",
            },
            "topic": "Statistics",
            "duration_minutes": 50,
            "requested_by": "test@163.com",
        }
        client.post("/booking/", json=request_data)
        # Get the latest request using the list requests endpoint
        response_get = client.get("/booking/")
        response_data_get = response_get.json().get("bookings")
        new_record = response_data_get[-1]
        # Reject the request, using the reject request endpoint; the response should be an updated BookingResponse instance
        response_reject = client.post("/booking/reject", json={"id": new_record["id"]})
        assert response_reject.status_code == 200
        response_data_reject = response_reject.json()
        assert response_data_reject["id"] == new_record["id"]
        assert response_data_reject["status"] == "rejected"

    def test_delete_request(self, client: TestClient, database_session: Session) -> None:
        """
        Test for the delete request endpoint.

        - Given an existing request in the database.
        - When the client (speaker) wishes to delete a specific request.
        - Then the response should be a 200 OK status code with a BookingResponse instance containing the deleted request data.
        """
        # Submit a request using the submit request endpoint
        request_data = {
            "event_time": "2024-10-03T05:07:54.259000",
            "address": {
                "street": "123 Main St",
                "city": "London",
                "state": None,
                "country": "United Kingdom",
            },
            "topic": "Statistics",
            "duration_minutes": 35,
            "requested_by": "test@hotmail.com",
        }
        client.post("/booking/", json=request_data)
        # Get the latest request using the list requests endpoint
        response_get = client.get("/booking/")
        response_data_get = response_get.json().get("bookings")
        new_record = response_data_get[-1]
        # Delete the request, using the delete request endpoint; the response should be a BookingResponse instance containing the deleted request data
        response_delete = client.delete(f"/booking/{new_record['id']}")
        assert response_delete.status_code == 200
        response_data_delete = response_delete.json()
        assert response_data_delete["id"] == new_record["id"]
        assert response_data_delete["event_time"] == request_data["event_time"]
        assert response_data_delete["address"] == request_data["address"]
        assert response_data_delete["topic"] == request_data["topic"]
        assert response_data_delete["duration_minutes"] == request_data["duration_minutes"]
        assert response_data_delete["requested_by"] == request_data["requested_by"]
        assert response_data_delete["status"] == "pending"

    @pytest.mark.parametrize("endpoint", ["/booking/accept", "/booking/reject"])
    def test_invalid_id(self, client: TestClient, database_session: Session, endpoint: str) -> None:
        """
        Test for both accept and reject request endpoints with an invalid ID.

        - Given an invalid request ID.
        - When the client (speaker) wishes to accept or reject a specific request.
        - Then the response should be a 404 Not Found error.
        """
        response = client.post(endpoint, json={"id": 999})
        assert response.status_code == 404
