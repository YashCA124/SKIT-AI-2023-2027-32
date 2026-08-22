from enum import Enum

class BookingStatus(str, Enum):
    BOOKING_COMPLETED = 'COMPLETED'
    BOOKING_ACTIVE = 'ACTIVE'
    SPOT_AVAILABLE = 'A'
    SPOT_BOOKED = 'O'
