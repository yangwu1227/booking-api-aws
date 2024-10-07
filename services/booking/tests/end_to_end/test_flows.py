import os
from datetime import datetime, timedelta
from typing import Dict, Union
from urllib.parse import urljoin

import pytest
import requests

CustomResponse = Dict[str, Union[str, int, Dict[str, str]]]


@pytest.fixture(scope="module")
def domain() -> str:
    """
    Fixture to get the domain of the booking service from the environment variable.

    Returns
    -------
    str
        The domain of the booking service.
    """
    return "https://dev.dashwu.xyz/"


@pytest.fixture(scope="module")
def get_auth_token(domain: str) -> str:
    """
    Get the authentication token for accessing the booking service.

    Returns
    -------
    str
        The Bearer token required for making authenticated requests.
    """
    # Get the admin password from environment variables
    password = os.getenv("ADMIN_PASSWORD")

    response = requests.post(
        urljoin(domain, "/token"),
        data={"username": "admin", "password": password},
    )

    assert response.status_code == 200, "Failed to obtain authentication token"
    token_data = response.json()
    return token_data["access_token"]


def booking_submission(domain: str, auth_token: str) -> CustomResponse:
    """
    Submit a booking request to the booking service at the specified endpoint.

    Parameters
    ----------
    domain : str
        The domain of the booking service.
    auth_token : str
        The Bearer token for authentication.

    Returns
    -------
    CustomResponse
        The response JSON from the booking service after submitting the booking.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(
        urljoin(domain, "/booking/"),
        json={
            "event_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "address": {
                "street": "123 Main Street",
                "city": "Anytown",
                "state": "NY",
                "country": "USA",
            },
            "topic": "Statistical Learning",
            "duration_minutes": 60,
            "requested_by": "test@gmail.com",
        },
        headers=headers,
    )
    assert response.status_code == 201, "Booking submission failed"
    return response.json()


def list_bookings(
    domain: str, booking_response: CustomResponse, auth_token: str
) -> Union[CustomResponse, None]:
    """
    List all bookings from the booking service at the specified endpoint, ensuring that the submitted booking is listed.

    Parameters
    ----------
    domain : str
        The domain of the booking service.
    booking_response : CustomResponse
        The response JSON from the booking service after submitting the booking.
    auth_token : str
        The Bearer token for authentication.

    Returns
    -------
    Union[CustomResponse, None]
        The response JSON from the booking service after listing the bookings.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(urljoin(domain, "/booking/"), headers=headers)
    assert response.status_code == 200, "Booking listing failed"
    bookings_list = response.json().get("bookings", [])

    for booking in bookings_list:
        if booking["event_time"] == booking_response["event_time"]:
            assert booking["address"] == booking_response["address"]
            assert booking["topic"] == booking_response["topic"]
            assert booking["duration_minutes"] == booking_response["duration_minutes"]
            assert booking["requested_by"] == booking_response["requested_by"]
            assert booking["status"] == "pending"
            return booking

    assert False, "Submitted booking not found in the list of bookings"


def update_booking_status(domain: str, id: int, action: str, auth_token: str) -> None:
    """
    Update the booking status (accept or reject) at the specified endpoint.

    Parameters
    ----------
    domain : str
        The domain of the booking service.
    id : int
        The unique identifier of the booking to accept or reject.
    action : str
        The action to perform on the booking, which can be either "accept" or "reject".
    auth_token : str
        The Bearer token for authentication.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    assert action in ["accept", "reject"], "Invalid action. Must be 'accept' or 'reject'."
    response = requests.post(
        urljoin(domain, f"/booking/{action}/"), json={"id": id}, headers=headers
    )
    assert response.status_code == 200, f"Booking {action} failed"
    booking_response = response.json()
    expected_status = "accepted" if action == "accept" else "rejected"
    assert booking_response["status"] == expected_status, f"Booking {action} status mismatch"
    return booking_response


def delete_booking(domain: str, id: int, auth_token: str) -> None:
    """
    Delete a booking request from the booking service at the specified endpoint.

    Parameters
    ----------
    domain : str
        The domain of the booking service.
    id : int
        The unique identifier of the booking request to delete.
    auth_token : str
        The Bearer token for authentication.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.delete(urljoin(domain, f"/booking/{id}/"), headers=headers)
    assert response.status_code == 200, "Booking deletion failed"


@pytest.mark.parametrize("action", ["accept", "reject"])
def test_booking_flow(action: str, domain: str, get_auth_token: str) -> None:
    """
    Test the end-to-end flow of booking submission, listing, and either accepting or rejecting the booking.
    """
    auth_token = get_auth_token
    booking_response_without_id = booking_submission(domain, auth_token)
    booking_response_with_id = list_bookings(domain, booking_response_without_id, auth_token)
    update_booking_status(domain, booking_response_with_id["id"], action, auth_token)
    delete_booking(domain, booking_response_with_id["id"], auth_token)
