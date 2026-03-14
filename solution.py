## Student Name: Mateo Pedraza
## Student ID: 218659094

"""
Task B: Event Registration with Waitlist (Stub)
In this lab, you will design and implement an Event Registration with Waitlist system using an LLM assistant as your primary programming collaborator. 
You are asked to implement a Python module that manages registration for a single event with a fixed capacity. 
The system must:
•	Accept a fixed capacity.
•	Register users until capacity is reached.
•	Place additional users into a FIFO waitlist.
•	Automatically promote the earliest waitlisted user when a registered user cancels.
•	Prevent duplicate registrations.
•	Allow users to query their current status.

The system must ensure that:
•	The number of registered users never exceeds capacity.
•	Waitlist ordering preserves FIFO behavior.
•	Promotions occur deterministically under identical operation sequences.

The module must preserve the following invariants:
•	A user may not appear more than once in the system.
•	A user may not simultaneously exist in multiple states.
•	The system state must remain consistent after every operation.

The system must correctly handle non-trivial scenarios such as:
•	Multiple cancellations in sequence.
•	Users attempting to re-register after canceling.
•	Waitlisted users canceling before promotion.
•	Capacity equal to zero.
•	Simultaneous or rapid consecutive operations.
•	Queries during state transitions.

The output consists of the updated registration state and ordered lists of registered and waitlisted users after each operation.
"""

from dataclasses import dataclass
from typing import List, Optional


class DuplicateRequest(Exception):
    """Raised if a user tries to register but is already registered or waitlisted."""
    pass


class NotFound(Exception):
    """Raised if a user cannot be found for cancellation (if required by handout)."""
    pass


@dataclass(frozen=True)
class UserStatus:
    """
    state:
      - "registered"
      - "waitlisted"
      - "none"
    position: 1-based waitlist position if waitlisted; otherwise None
    """
    state: str
    position: Optional[int] = None


@dataclass(frozen=True)
class OperationResult:
    """
    Returned by register() and cancel().
    operation_success: True if the operation completed as intended
    status_message: human-readable description of the outcome
    registered_users: ordered list of currently registered user IDs
    waitlisted_users: ordered list of currently waitlisted user IDs (FIFO)
    """
    operation_success: bool
    status_message: str
    registered_users: List[str]
    waitlisted_users: List[str]


class EventRegistration:
    """
    Deterministic event registration system with FIFO waitlist.
    """

    def __init__(self, capacity: int) -> None:
        """
        Args:
            capacity: maximum number of registered users (>= 0)
        """
        if not isinstance(capacity, int) or capacity < 0:
            raise ValueError("capacity must be a non-negative integer")

        self.capacity = capacity
        self._registered: List[str] = []
        self._waitlist: List[str] = []

    def _validate_user_id(self, user_id: str) -> None:
        if not isinstance(user_id, str) or user_id.strip() == "":
            raise ValueError("user_id must be a non-empty string")

    def _exists(self, user_id: str) -> bool:
        return user_id in self._registered or user_id in self._waitlist

    def _result(self, operation_success: bool, status_message: str) -> OperationResult:
        return OperationResult(
            operation_success=operation_success,
            status_message=status_message,
            registered_users=self._registered.copy(),
            waitlisted_users=self._waitlist.copy(),
        )

    def register(self, user_id: str) -> OperationResult:
        """
        Register a user:
          - if capacity available -> registered
          - else -> waitlisted (FIFO)

        Returns OperationResult with operation_success = False for duplicates
        instead of raising. Covers both registered and waitlisted duplicates.
        Constraints: C1, C3, C4, C9, C10, C11
        """
        self._validate_user_id(user_id)

        if self._exists(user_id):
            return self._result(False, f"{user_id} is already in the system")

        if len(self._registered) < self.capacity:
            self._registered.append(user_id)
            return self._result(True, f"{user_id} registered successfully")

        self._waitlist.append(user_id)
        return self._result(True, f"{user_id} added to waitlist")

    def cancel(self, user_id: str) -> OperationResult:
        """
        Cancel a user:
          - if registered -> remove and promote earliest waitlisted user (if any)
          - if waitlisted -> remove from waitlist, no promotion
          - if not found -> operation_success = False

        Promotion message names both the cancelled and promoted user (C6).
        No-promotion message omits promotion text (C6).
        Returns OperationResult in all cases instead of raising (C7).
        Constraints: C1, C5, C6, C7, C11
        """
        self._validate_user_id(user_id)

        if user_id in self._registered:
            self._registered.remove(user_id)

            if self.capacity > 0 and self._waitlist:
                promoted = self._waitlist.pop(0)
                self._registered.append(promoted)
                return self._result(
                    True,
                    f"{user_id} cancelled; {promoted} promoted from waitlist",
                )

            return self._result(True, f"{user_id} cancelled successfully")

        if user_id in self._waitlist:
            self._waitlist.remove(user_id)
            return self._result(True, f"{user_id} cancelled successfully")

        return self._result(False, f"{user_id} not found")

    def status(self, user_id: str) -> UserStatus:
        """
        Return status of a user:
          - registered -> state = "registered", position = None
          - waitlisted -> state = "waitlisted", position = 1-based index
          - unknown   -> state = "none", position = None
        Constraints: C12
        """
        self._validate_user_id(user_id)

        if user_id in self._registered:
            return UserStatus("registered")

        if user_id in self._waitlist:
            return UserStatus("waitlisted", self._waitlist.index(user_id) + 1)

        return UserStatus("none")

    def snapshot(self) -> dict:
        """
        Return a deterministic snapshot of internal state.
        """
        return {
            "registered": self._registered.copy(),
            "waitlist": self._waitlist.copy(),
        }