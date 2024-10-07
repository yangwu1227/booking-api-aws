from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.auth import (
    get_current_active_user,
    get_current_admin,
    get_current_user_or_admin,
)
from app.db import get_database_session
from app.models import *
from app.models.db_models import DatabaseOperations

router = APIRouter()


@router.post(
    "/",
    status_code=201,
    response_model=BookingResponse,
    dependencies=[Depends(get_current_user_or_admin), Depends(get_current_active_user)],
)
async def submit_request(
    submission: SubmissionRequest, database_session: Session = Depends(get_database_session)
) -> BookingResponse:
    """
    Submit a new booking request.

    This endpoint allows the submission of a new booking request. The booking will be stored
    in the database and returned with a status of "pending".

    Parameters
    ----------
    submission : SubmissionRequest
        The request data containing event details such as event time, address, topic, duration, and the requester.
    database_session : Session, optional
        A SQLAlchemy database session for interacting with the database, by default Depends(get_database_session).

    Returns
    -------
    BookingResponse
        The submitted booking request with a status of "pending".
    """
    booking_response = BookingResponse(
        event_time=submission.event_time,
        address=submission.address,
        topic=submission.topic,
        duration_minutes=submission.duration_minutes,
        requested_by=submission.requested_by,
        status=RequestStatus.pending,
    )
    db_operations = DatabaseOperations(database_session)
    db_operations.save_booking(booking_response)
    return booking_response


@router.get(
    "/",
    status_code=200,
    response_model=BookingResponseList,
    dependencies=[Depends(get_current_admin), Depends(get_current_active_user)],
)
async def list_requests(
    database_session: Session = Depends(get_database_session),
) -> BookingResponseList:
    """
    Retrieve a list of all booking requests.

    This endpoint fetches and returns a list of all the booking requests from the database.
    Each booking is returned with its details, including its current status.

    Parameters
    ----------
    database_session : Session, optional
        A SQLAlchemy database session for interacting with the database, by default Depends(get_database_session).

    Returns
    -------
    BookingResponseList
        A list of all booking requests.
    """
    db_operations = DatabaseOperations(database_session)
    booking_responses = db_operations.list_bookings()
    return BookingResponseList(
        bookings=[booking_response for booking_response in booking_responses]
    )


@router.post(
    "/accept/",
    status_code=200,
    response_model=BookingResponse,
    dependencies=[Depends(get_current_admin), Depends(get_current_active_user)],
)
async def accept_request(
    accept_response: AcceptRequest, database_session: Session = Depends(get_database_session)
) -> BookingResponse:
    """
    Accept a booking request.

    This endpoint allows the acceptance of a booking request by its ID.
    Once accepted, the status of the booking is updated to "accepted".

    Parameters
    ----------
    accept_response : AcceptRequest
        The ID of the booking request to accept.
    database_session : Session, optional
        A SQLAlchemy database session for interacting with the database, by default Depends(get_database_session).

    Returns
    -------
    BookingResponse
        The updated booking request with a status of "accepted".
    """
    db_operations = DatabaseOperations(database_session)
    booking_response = db_operations.list_booking_by_id(accept_response.id)
    # Accept the booking request
    booking_response.accept()
    db_operations.save_booking(booking_response)
    return booking_response


@router.post(
    "/reject/",
    status_code=200,
    response_model=BookingResponse,
    dependencies=[Depends(get_current_admin), Depends(get_current_active_user)],
)
async def reject_request(
    reject_response: RejectRequest, database_session: Session = Depends(get_database_session)
) -> BookingResponse:
    """
    Reject a booking request.

    This endpoint allows the rejection of a booking request by its ID.
    Once rejected, the status of the booking is updated to "rejected".

    Parameters
    ----------
    reject_response : RejectRequest
        The ID of the booking request to reject.
    database_session : Session, optional
        A SQLAlchemy database session for interacting with the database, by default Depends(get_database_session).

    Returns
    -------
    BookingResponse
        The updated booking request with a status of "rejected".
    """
    db_operations = DatabaseOperations(database_session)
    booking_response = db_operations.list_booking_by_id(reject_response.id)
    # Reject the booking request
    booking_response.reject()
    db_operations.save_booking(booking_response)
    return booking_response


@router.delete(
    "/{id}/",
    status_code=200,
    response_model=BookingResponse,
    dependencies=[Depends(get_current_admin), Depends(get_current_active_user)],
)
async def delete_request(
    id: Annotated[int, Path(title="The ID of the booking request to delete", gt=0)],
    database_session: Session = Depends(get_database_session),
) -> BookingResponse:
    """
    Delete a booking request.

    This endpoint allows the deletion of a booking request by its ID.
    Once deleted, the request is removed from the database.

    Parameters
    ----------
    delete_request : DeleteRequest
        The request object containing the ID of the booking to delete.
    database_session : Session, optional
        A SQLAlchemy database session for interacting with the database, by default Depends(get_database_session).

    Returns
    -------
    BookingResponse
        The response object for the deleted booking request.
    """
    db_operations = DatabaseOperations(database_session)
    booking_response = db_operations.delete_booking_by_id(id)
    return booking_response
