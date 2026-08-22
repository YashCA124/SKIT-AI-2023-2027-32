from enum import Enum

class AvailableStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    PENDING = 'PENDING'
    BLOCK = 'BLOCK'
    DELETE = 'DELETE'