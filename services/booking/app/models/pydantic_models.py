from datetime import datetime
from enum import Enum
from typing import List

import pycountry
from pydantic import (
    BaseModel,
    EmailStr,
    PositiveInt,
    StringConstraints,
    field_validator,
)
from typing_extensions import Annotated, Optional


class Address(BaseModel):
    """
    Address model for booking service.

    Attributes
    ----------
    street : str
        The street name of the address.
    city : str
        The city name of the address.
    state : str
        The state or province name of the address.
    country : str
        The country name of the address.
    """

    street: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    city: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    state: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]] = None
    country: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        try:
            # Perform a fuzzy search to find the country
            country = pycountry.countries.search_fuzzy(v)[0]
            # Replace the input with the official country name
            return country.name  # type: ignore[attr-defined]
        except LookupError:
            raise ValueError(f"'{v}' cannot be matched to any country")


class RequestStatus(str, Enum):
    """
    Status model for booking service.
    """

    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class BookingID(BaseModel):
    """
    BookingID model for booking service.

    Attributes
    ----------
    id : int
        The unique identifier of the booking request.
    """

    id: Optional[int] = None


class BookingResponse(BookingID):
    """
    BookingResponse model for booking service.

    Attributes
    ----------
    id : int
        The unique identifier of the booking request.
    event_time : datetime
        The date and time of the event.
    address : Address
        The address of the event.
    topic : str
        The topic of the event.
    duration_minutes : PositiveInt
        The duration of the event in minutes.
    requested_by : EmailStr
        The email address of the person who requested the event.
    status : str
        The status of the booking request, i.e., pending, approved, or rejected.
    """

    event_time: datetime
    address: Address
    topic: Annotated[str, StringConstraints(strip_whitespace=True)]
    duration_minutes: PositiveInt
    requested_by: EmailStr
    status: RequestStatus

    def accept(self) -> None:
        """
        Accept the booking request.
        """
        self.status = RequestStatus.accepted

    def reject(self) -> None:
        """
        Reject the booking request.
        """
        self.status = RequestStatus.rejected


class BookingResponseList(BaseModel):
    """
    BookingResponseList model for booking service. This model is used to return a list of booking responses.
    """

    bookings: List[BookingResponse]


class SubmissionRequest(BaseModel):
    """
    SubmissionRequest model for booking service.

    Attributes
    ----------
    event_time : datetime
        The date and time of the event.
    address : Address
        The address of the event.
    topic : str
        The topic of the event.
    duration_minutes : PositiveInt
        The duration of the event in minutes.
        The email address of the person who requested the event.
    """

    event_time: datetime
    address: Address
    topic: Annotated[str, StringConstraints(strip_whitespace=True)]
    duration_minutes: PositiveInt
    requested_by: EmailStr


class AcceptRequest(BookingID):
    """
    AcceptRequest model for booking service.

    Attributes
    ----------
    id : int
        The unique identifier of the accepted booking request.
    """


class RejectRequest(BookingID):
    """
    RejectRequest model for booking service.

    Attributes
    ----------
    id : int
        The unique identifier of the rejected booking request.
    """
