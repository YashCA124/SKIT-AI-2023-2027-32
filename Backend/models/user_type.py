from enum import Enum

class UserType(str, Enum):
    PARKING_USER = 'U'
    PARKING_MERCHANT = 'M'
    ADMIN = 'A'