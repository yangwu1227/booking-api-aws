from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.pydantic_models import Address, BookingResponse


class TestAddress(object):
    """
    Test the Address model in the booking service.
    """

    @pytest.mark.parametrize(
        "street, city, state, country, expected_country",
        [
            # Valid address
            ("1234 Main St", "San Francisco", "CA", "USA", "United States"),
            # Valid address with different country name
            ("1234 Main St", "Tokyo", None, "JP", "Japan"),
            # Valid address with different country name
            ("1234 Main St", "London", None, "Great Britain", "United Kingdom"),
        ],
        scope="function",
    )
    def test_address_attributes(self, street, city, state, country, expected_country) -> None:
        """
        Test the attributes of the Address model.
        """
        address = Address(
            street=street,
            city=city,
            state=state,
            country=country,
        )

        assert address.street == street
        assert address.city == city
        assert address.state == state
        assert address.country == expected_country

    @pytest.mark.parametrize(
        "street, city, state, country",
        [
            # Invalid country (non-existent country)
            ("1234 Main St", "San Francisco", "CA", "InvalidCountry"),
            # Empty street
            ("", "San Francisco", "CA", "USA"),
            # Empty city
            ("1234 Main St", "", "CA", "USA"),
            # Empty state
            ("1234 Main St", "San Francisco", "", "USA"),
            # Empty country
            ("1234 Main St", "San Francisco", "CA", ""),
            # Invalid numeric country
            ("1234 Main St", "San Francisco", "CA", 123),
        ],
        scope="function",
    )
    def test_invalid_address_inputs(self, street, city, state, country) -> None:
        """
        Test invalid inputs for the Address model.
        """
        with pytest.raises(ValidationError):
            Address(
                street=street,
                city=city,
                state=state,
                country=country,
            )


class TestBookingResponse(object):
    """
    Test the BookingResponse model in the booking service.
    """

    @pytest.mark.parametrize(
        "id, event_time, address, topic, duration_minutes, requested_by, status",
        [
            (
                12,
                datetime.now(),
                Address(street="1234 Main St", city="San Francisco", state="CA", country="USA"),
                "Machine Learning and AI",
                60,
                "test@gmail.com",
                "pending",
            ),
            (
                17,
                datetime(2022, 1, 1, 12, 0),
                Address(street="1234 Main St", city="Toronto", state="Ontario", country="Canada"),
                "Statistics",
                120,
                "requester@yahoo.com",
                "accepted",
            ),
            (
                27,
                datetime(2024, 12, 27, 0, 0),
                Address(street="1234 Main St", city="Tokyo", state=None, country="Japan"),
                "Data Engineering",
                90,
                "team@outlook.com",
                "rejected",
            ),
        ],
        scope="function",
    )
    def test_booking_request_attributes(
        self, id, event_time, address, topic, duration_minutes, requested_by, status
    ) -> None:
        """
        Test the attributes of the BookingResponse model.
        """
        booking_request = BookingResponse(
            id=id,
            event_time=event_time,
            address=address,
            topic=topic,
            duration_minutes=duration_minutes,
            requested_by=requested_by,
            status=status,
        )

        assert booking_request.id == id
        assert booking_request.event_time == event_time
        assert booking_request.address == address
        assert booking_request.topic == topic
        assert booking_request.duration_minutes == duration_minutes
        assert booking_request.requested_by == requested_by
        assert booking_request.status == status

    @pytest.mark.parametrize(
        "id, event_time, address, topic, duration_minutes, requested_by, status",
        [
            # Invalid status
            (
                12,
                datetime.now(),
                Address(street="1234 Main St", city="San Francisco", state="CA", country="USA"),
                "Machine Learning",
                60,
                "test@gmail.com",
                "invalid_status",
            ),
            # Invalid duration (0 minutes)
            (
                12,
                datetime.now(),
                Address(street="1234 Main St", city="San Francisco", state="CA", country="USA"),
                "Machine Learning",
                0,
                "test@gmail.com",
                "pending",
            ),
            # Invalid email
            (
                12,
                datetime.now(),
                Address(street="1234 Main St", city="San Francisco", state="CA", country="USA"),
                "Machine Learning",
                60,
                "invalid_email",
                "pending",
            ),
        ],
        scope="function",
    )
    def test_invalid_booking_request_inputs(
        self, id, event_time, address, topic, duration_minutes, requested_by, status
    ) -> None:
        """
        Test invalid inputs for the BookingResponse model.
        """
        with pytest.raises(ValidationError):
            BookingResponse(
                id=id,
                event_time=event_time,
                address=address,
                topic=topic,
                duration_minutes=duration_minutes,
                requested_by=requested_by,
                status=status,
            )
