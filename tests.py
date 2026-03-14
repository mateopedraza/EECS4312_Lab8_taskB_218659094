import pytest

from solution import EventRegistration, UserStatus, OperationResult


# Covers C3, C10, C11, AC1
def test_register_into_available_capacity_returns_success_and_registered_snapshot():
    er = EventRegistration(capacity=3)
    er.register("u1")
    er.register("u2")

    result = er.register("u3")

    assert isinstance(result, OperationResult)
    assert result.operation_success is True
    assert result.status_message == "u3 registered successfully"
    assert result.registered_users == ["u1", "u2", "u3"]
    assert result.waitlisted_users == []


# Covers C1, C5, C6, C11, AC2, AC8
def test_cancel_registered_promotes_waitlist_index_zero_and_message_names_both_users():
    er = EventRegistration(capacity=2)
    er.register("r1")
    er.register("r2")
    er.register("w1")
    er.register("w2")

    result = er.cancel("r1")

    assert result.operation_success is True
    assert "r1" in result.status_message
    assert "w1" in result.status_message
    assert "promoted" in result.status_message
    assert result.registered_users == ["r2", "w1"]
    assert result.waitlisted_users == ["w2"]


# Covers C3, C4, C10, C11, AC3
def test_register_when_full_appends_to_waitlist_and_returns_success():
    er = EventRegistration(capacity=1)
    er.register("u1")

    result = er.register("u2")

    assert result.operation_success is True
    assert result.status_message == "u2 added to waitlist"
    assert result.registered_users == ["u1"]
    assert result.waitlisted_users == ["u2"]


# Covers C7, C8, C9, C11, AC4
def test_duplicate_register_for_registered_user_returns_failure_and_state_unchanged():
    er = EventRegistration(capacity=2)
    er.register("u1")
    er.register("u2")
    before = er.snapshot()

    result = er.register("u1")

    assert result.operation_success is False
    assert result.status_message == "u1 is already in the system"
    assert result.registered_users == before["registered"]
    assert result.waitlisted_users == before["waitlist"]


# Covers C7, C8, C11, AC5, EC3
def test_cancel_unknown_user_returns_failure_and_state_unchanged():
    er = EventRegistration(capacity=2)
    er.register("u1")
    before = er.snapshot()

    result = er.cancel("ghost")

    assert result.operation_success is False
    assert result.status_message == "ghost not found"
    assert result.registered_users == before["registered"]
    assert result.waitlisted_users == before["waitlist"]


# Covers C3, C10, C11, AC6, EC1
def test_capacity_zero_places_all_users_on_waitlist_in_order():
    er = EventRegistration(capacity=0)

    r1 = er.register("u1")
    r2 = er.register("u2")
    r3 = er.register("u3")

    assert r1.operation_success is True
    assert r2.operation_success is True
    assert r3.operation_success is True

    assert r1.registered_users == []
    assert r1.waitlisted_users == ["u1"]

    assert r2.registered_users == []
    assert r2.waitlisted_users == ["u1", "u2"]

    assert r3.registered_users == []
    assert r3.waitlisted_users == ["u1", "u2", "u3"]


# Covers C1, C5, C6, C8, C11, AC7
def test_registered_cancel_replayed_from_fresh_state_is_deterministic_each_time():
    outcomes = []

    for _ in range(3):
        er = EventRegistration(capacity=2)
        er.register("r1")
        er.register("r2")
        er.register("w1")
        er.register("w2")
        er.register("w3")

        result = er.cancel("r1")
        outcomes.append(
            (
                result.operation_success,
                result.status_message,
                result.registered_users,
                result.waitlisted_users,
            )
        )

    assert outcomes[0] == outcomes[1] == outcomes[2]
    assert outcomes[0][2] == ["r2", "w1"]
    assert outcomes[0][3] == ["w2", "w3"]


# Covers C7, C8, C9, C11, AC9, EC4
def test_duplicate_register_for_waitlisted_user_returns_failure_and_state_unchanged():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")
    before = er.snapshot()

    result = er.register("u2")

    assert result.operation_success is False
    assert result.status_message == "u2 is already in the system"
    assert result.registered_users == before["registered"]
    assert result.waitlisted_users == before["waitlist"]


# Covers C6, C11, AC10, EC5
def test_cancel_waitlisted_user_removes_from_queue_without_promotion_text():
    er = EventRegistration(capacity=1)
    er.register("r1")
    er.register("w1")
    er.register("w2")

    result = er.cancel("w1")

    assert result.operation_success is True
    assert result.status_message == "w1 cancelled successfully"
    assert "promoted" not in result.status_message
    assert result.registered_users == ["r1"]
    assert result.waitlisted_users == ["w2"]


# Covers C10, C11, AC11, EC6
def test_previously_cancelled_user_can_reregister_as_new_entry():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.cancel("u1")

    result = er.register("u1")

    assert result.operation_success is True
    assert result.status_message == "u1 registered successfully"
    assert result.registered_users == ["u1"]
    assert result.waitlisted_users == []


# Covers C6, C11, AC12, EC2
def test_cancel_registered_with_empty_waitlist_removes_user_and_has_no_promotion_text():
    er = EventRegistration(capacity=2)
    er.register("u1")

    result = er.cancel("u1")

    assert result.operation_success is True
    assert result.status_message == "u1 cancelled successfully"
    assert "promoted" not in result.status_message
    assert result.registered_users == []
    assert result.waitlisted_users == []


# Covers C12, AC13
def test_status_for_registered_user_returns_registered_and_no_position():
    er = EventRegistration(capacity=2)
    er.register("u1")

    status = er.status("u1")

    assert isinstance(status, UserStatus)
    assert status.state == "registered"
    assert status.position is None


# Covers C12, AC14
def test_status_for_waitlisted_user_returns_waitlisted_and_one_based_position():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")
    er.register("u3")

    status = er.status("u3")

    assert status.state == "waitlisted"
    assert status.position == 2


# Covers C8, C12, AC15
def test_unknown_user_status_is_identical_across_repeated_calls_from_same_state():
    er = EventRegistration(capacity=1)

    s1 = er.status("ghost")
    s2 = er.status("ghost")
    s3 = er.status("ghost")

    assert s1.state == "none"
    assert s1.position is None

    assert s2.state == "none"
    assert s2.position is None

    assert s3.state == "none"
    assert s3.position is None

    assert s1 == s2 == s3


# Covers C2, C11, AC2
def test_registered_list_preserves_insertion_order_except_for_cancel_and_promotion():
    er = EventRegistration(capacity=3)
    er.register("u1")
    er.register("u2")
    er.register("u3")
    er.register("u4")

    before_cancel = er.snapshot()
    assert before_cancel["registered"] == ["u1", "u2", "u3"]

    result = er.cancel("u2")

    assert result.registered_users == ["u1", "u3", "u4"]
    assert result.waitlisted_users == []


# Covers C7, C8, C11, AC5, EC3
def test_repeated_cancel_unknown_user_uses_same_message_template_and_fields():
    er = EventRegistration(capacity=1)

    r1 = er.cancel("ghost")
    r2 = er.cancel("ghost")

    assert r1.operation_success is False
    assert r2.operation_success is False
    assert r1.status_message == "ghost not found"
    assert r2.status_message == "ghost not found"
    assert r1.registered_users == r2.registered_users == []
    assert r1.waitlisted_users == r2.waitlisted_users == []


# Covers C11, AC1
def test_operation_result_has_exact_expected_field_names():
    er = EventRegistration(capacity=1)

    result = er.register("u1")

    assert set(result.__dataclass_fields__.keys()) == {
        "operation_success",
        "status_message",
        "registered_users",
        "waitlisted_users",
    }