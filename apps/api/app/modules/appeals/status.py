from enum import StrEnum


class AppealStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RESOLVED = "resolved"


RESOLUTION_DECISIONS = {
    AppealStatus.ACCEPTED.value,
    AppealStatus.REJECTED.value,
}
