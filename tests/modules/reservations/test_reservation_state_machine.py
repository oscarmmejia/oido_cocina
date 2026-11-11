"""Pruebas de la máquina de estados de reservas (ST-RES-03.6)."""

import pytest

pytest.importorskip(
    "app.models.enums",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from app.core.kernel.errors import AppError  # noqa: E402
from app.models.enums import ReservationStatus  # noqa: E402
from app.modules.reservations.services.state_machine import (  # noqa: E402
    ALLOWED_TRANSITIONS,
    FINAL_STATUSES,
    allowed_targets,
    can_transition,
    ensure_transition_allowed,
    is_final_status,
)

VALID_TRANSITIONS = [
    (ReservationStatus.PENDING, ReservationStatus.CONFIRMED),
    (ReservationStatus.PENDING, ReservationStatus.CANCELLED),
    (ReservationStatus.CONFIRMED, ReservationStatus.SEATED),
    (ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED),
    (ReservationStatus.CONFIRMED, ReservationStatus.NO_SHOW),
    (ReservationStatus.SEATED, ReservationStatus.COMPLETED),
]

INVALID_TRANSITIONS = [
    (ReservationStatus.PENDING, ReservationStatus.SEATED),
    (ReservationStatus.PENDING, ReservationStatus.COMPLETED),
    (ReservationStatus.PENDING, ReservationStatus.NO_SHOW),
    (ReservationStatus.CONFIRMED, ReservationStatus.PENDING),
    (ReservationStatus.CONFIRMED, ReservationStatus.COMPLETED),
    (ReservationStatus.SEATED, ReservationStatus.PENDING),
    (ReservationStatus.SEATED, ReservationStatus.CONFIRMED),
    (ReservationStatus.SEATED, ReservationStatus.CANCELLED),
    (ReservationStatus.SEATED, ReservationStatus.NO_SHOW),
]


def test_allowed_transitions_cover_every_status():
    assert set(ALLOWED_TRANSITIONS) == set(ReservationStatus)


@pytest.mark.parametrize("current,target", VALID_TRANSITIONS)
def test_valid_transitions_are_allowed(current, target):
    assert can_transition(current, target)
    assert target in allowed_targets(current)
    assert ensure_transition_allowed(current, target) is None


@pytest.mark.parametrize("current,target", INVALID_TRANSITIONS)
def test_invalid_transitions_are_rejected(current, target):
    assert not can_transition(current, target)

    with pytest.raises(AppError) as error:
        ensure_transition_allowed(current, target)

    assert error.value.code == "INVALID_RESERVATION_TRANSITION"
    assert error.value.status_code == 409


@pytest.mark.parametrize("status", sorted(FINAL_STATUSES))
def test_final_states_have_no_allowed_targets(status):
    assert is_final_status(status)
    assert allowed_targets(status) == frozenset()


@pytest.mark.parametrize("status", sorted(FINAL_STATUSES))
@pytest.mark.parametrize("target", list(ReservationStatus))
def test_final_states_are_immutable(status, target):
    with pytest.raises(AppError) as error:
        ensure_transition_allowed(status, target)

    assert error.value.code == "INVALID_RESERVATION_TRANSITION"
    assert error.value.status_code == 409


@pytest.mark.parametrize(
    "status",
    [
        ReservationStatus.PENDING,
        ReservationStatus.CONFIRMED,
        ReservationStatus.SEATED,
    ],
)
def test_active_states_are_not_final(status):
    assert not is_final_status(status)


@pytest.mark.parametrize("status", list(ReservationStatus))
def test_self_transitions_are_rejected(status):
    assert not can_transition(status, status)

    with pytest.raises(AppError) as error:
        ensure_transition_allowed(status, status)

    assert error.value.code == "INVALID_RESERVATION_TRANSITION"


def test_can_transition_matches_full_matrix():
    for current in ReservationStatus:
        for target in ReservationStatus:
            allowed = target in ALLOWED_TRANSITIONS[current]
            assert can_transition(current, target) is allowed


def test_string_statuses_are_accepted():
    assert can_transition("pending", "confirmed")
    assert ensure_transition_allowed("confirmed", "seated") is None
    assert is_final_status("cancelled")


def test_unknown_status_is_rejected():
    with pytest.raises(AppError) as error:
        ensure_transition_allowed("waitlisted", ReservationStatus.CONFIRMED)

    assert error.value.code == "INVALID_RESERVATION_TRANSITION"
    assert error.value.status_code == 409
