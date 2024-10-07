from typing import List, Union, cast

from fastapi import HTTPException
from sqlalchemy import JSON, Boolean, DateTime, Integer, SmallInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.models.pydantic_models import Address, BookingResponse


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models. See https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html#table-configuration-with-declarative for more information.
    """

    pass


class User(Base):
    """
    SQLAlchemy model representing a user in the application.

    This model maps to the "users" table in the database and stores user-related information, such as
    their username, full name, email, password, and role.

    Attributes
    ----------
    id : Mapped[int]
        The unique identifier for the user (primary key, auto-incremented).
    username : Mapped[str]
        The username of the user (unique, required, and indexed).
    hashed_password : Mapped[str]
        The hashed password used for authentication (required).
    disabled : Mapped[bool]
        Indicates whether the user account is disabled (default is False).
    role : Mapped[str]
        The role of the user, such as "admin" or "requester" (required).
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        """
        Provides a string representation of the User instance.

        Returns
        -------
        str
            A string that shows the username and role of the user.
        """
        return f"User(username={self.username}, role={self.role})"


class Booking(Base):
    """
    SQLAlchemy model representing a booking request record in the database.

    Attributes
    ----------
    id : Column[Integer]
        Unique identifier for the booking request (primary key).
    event_time : Column[DateTime]
        Date and time of the event associated with the booking request.
    address : Column[JSON]
        JSON field storing the address details for the booking.
    duration_minutes : Column[SmallInteger]
        Duration of the booking in minutes.
    topic : Column[String]
        Topic or subject of the booking request.
    requested_by : Column[String]
        Email address of the user who requested the booking.
    status : Column[String]
        Current status of the booking (maximum length 10), i.e., "pending", "approved", or "rejected".
    """

    __tablename__ = "booking_requests"

    id: Mapped[Integer] = mapped_column(
        Integer, primary_key=True, index=True, nullable=False, autoincrement=True
    )
    event_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    address: Mapped[JSON] = mapped_column(JSON, nullable=False)
    duration_minutes: Mapped[SmallInteger] = mapped_column(SmallInteger, nullable=False)
    topic: Mapped[String] = mapped_column(String, nullable=False)
    requested_by: Mapped[String] = mapped_column(String(100), nullable=False)
    status: Mapped[String] = mapped_column(String(10), nullable=False)

    def __repr__(self) -> str:
        """
        Provides a string representation of the `Booking instance.

        Returns
        -------
        str
            A string that shows key details about the booking request, including
            the event time, duration, topic, requestor, and status.
        """
        return f"Booking(event_time={self.event_time!r}, duration_minutes={self.duration_minutes!r}, topic={self.topic!r}, requested_by={self.requested_by!r}, status={self.status!r})"


class DatabaseOperations:
    """
    Class providing operations to interact with the Bookings table in the database.

    Parameters
    ----------
    session : Session
        SQLAlchemy session used for database transactions.

    Methods
    -------
    save_booking(booking)
        Saves a booking request to the database.
    list_bookings()
        Lists all booking requests in the database.
    list_booking_by_id(id)
        Fetches a specific booking request by its ID.
    delete_booking_by_id(id)
        Deletes a specific booking request by its ID.
    """

    def __init__(self, session: Session) -> None:
        """
        Initializes a new instance of the DatabaseOperations class.

        Parameters
        ----------
        session : Session
            An SQLAlchemy session used for interacting with the database.

        Returns
        -------
        None
        """
        self.session: Session = session

    def save_booking(self, booking: BookingResponse) -> None:
        """
        Saves a new booking request or merges an existing one into the database.

        Parameters
        ----------
        booking : BookingResponse
            The booking response object containing the details to save into the
            database.

        Returns
        -------
        None
        """
        # Create a new booking request record
        new_booking = Booking(
            id=booking.id,
            event_time=booking.event_time,
            address=booking.address.model_dump(),
            duration_minutes=booking.duration_minutes,
            topic=booking.topic,
            requested_by=booking.requested_by,
            status=booking.status,
        )
        # Save the record to the database
        self.session.merge(new_booking)
        self.session.commit()

    def list_bookings(self) -> List[BookingResponse]:
        """
        Retrieves a list of all booking requests from the database.

        Returns
        -------
        List[BookingResponse]
            A list of Pydantic models representing the booking responses, where
            each entry contains details of a single booking request.
        """
        bookings = self.session.query(Booking).all()
        return [
            BookingResponse(
                id=booking.id,  # type: ignore[arg-type]
                event_time=booking.event_time,  # type: ignore[arg-type]
                address=Address(**booking.address),  # type: ignore[arg-type]
                duration_minutes=booking.duration_minutes,  # type: ignore[arg-type]
                topic=booking.topic,  # type: ignore[arg-type]
                requested_by=booking.requested_by,  # type: ignore[arg-type]
                status=booking.status,  # type: ignore[arg-type]
            )
            for booking in bookings
        ]

    def list_booking_by_id(self, id: Union[int, None]) -> BookingResponse:
        """
        Retrieves a specific booking request from the database by its ID.

        Parameters
        ----------
        id : Union[int, None]
            The unique identifier of the booking request to retrieve.

        Returns
        -------
        BookingResponse
            A Pydantic model representing the booking response, including
            details such as event time, address, duration, topic, and status.
        """
        booking = self.session.query(Booking).filter(Booking.id == id).first()
        # Raise an HTTP 404 exception if the booking request is not found
        if booking is None:
            raise HTTPException(status_code=404, detail=f"Booking request with ID {id} not found.")
        return BookingResponse(
            id=booking.id,  # type: ignore[arg-type]
            event_time=booking.event_time,  # type: ignore[arg-type]
            address=Address(**booking.address),  # type: ignore[arg-type]
            duration_minutes=booking.duration_minutes,  # type: ignore[arg-type]
            topic=booking.topic,  # type: ignore[arg-type]
            requested_by=booking.requested_by,  # type: ignore[arg-type]
            status=booking.status,  # type: ignore[arg-type]
        )

    def delete_booking_by_id(self, id: Union[int, None]) -> BookingResponse:
        """
        Deletes a specific booking request from the database by its ID.

        Parameters
        ----------
        id : Union[int, None]
            The unique identifier of the booking request to delete.

        Returns
        -------
        BookingResponse
            A Pydantic model representing the booking response that was deleted.
        """
        booking = self.session.query(Booking).filter(Booking.id == id).first()
        # Raise an HTTP 404 exception if the booking request is not found
        if booking is None:
            raise HTTPException(status_code=404, detail=f"Booking request with ID {id} not found.")
        self.session.delete(booking)
        self.session.commit()
        return BookingResponse(
            id=booking.id,  # type: ignore[arg-type]
            event_time=booking.event_time,  # type: ignore[arg-type]
            address=Address(**booking.address),  # type: ignore[arg-type]
            duration_minutes=booking.duration_minutes,  # type: ignore[arg-type]
            topic=booking.topic,  # type: ignore[arg-type]
            requested_by=booking.requested_by,  # type: ignore[arg-type]
            status=booking.status,  # type: ignore[arg-type]
        )
