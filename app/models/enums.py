from enum import StrEnum


class TableLocation(StrEnum):
    INTERIOR = "interior"
    EXTERIOR = "exterior"
    BAR = "bar"


class OpeningPeriod(StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"


class MenuCollectionType(StrEnum):
    DAILY = "daily"
    SEASONAL = "seasonal"
    FIXED = "fixed"


class MenuDishRole(StrEnum):
    STARTER = "starter"
    MAIN = "main"
    DESSERT = "dessert"
    DRINK = "drink"
    OTHER = "other"


class ReservationStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SEATED = "seated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ReservationTableStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class JobPosition(StrEnum):
    COOK = "cook"
    WAITER = "waiter"
    MANAGER = "manager"
    HOST = "host"
    OTHER = "other"


class ScheduleStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class ShiftType(StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"
    SPLIT = "split"


class ShiftStatus(StrEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class TimeOffType(StrEnum):
    VACATION = "vacation"
    SICK_LEAVE = "sick_leave"
    PERSONAL = "personal"
    OTHER = "other"


class RequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class PriceEntityType(StrEnum):
    DISH = "dish"
    MENU = "menu"


def enum_check(column: str, enum_type: type[StrEnum]) -> str:
    """Genera la expresión SQL de un CHECK para un StrEnum."""

    values = ", ".join(f"'{item.value}'" for item in enum_type)
    return f"{column} IN ({values})"
