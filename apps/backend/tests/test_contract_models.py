"""Tests for the Pydantic models generated from the OpenAPI contract.

They pin the contract semantics that are easy to lose when generator settings change:
required-but-nullable fields, string length constraints and closed enums.
"""

import pytest
from pydantic import ValidationError

from app.generated.contract_models import (
    AssignmentCommand,
    HealthStatus,
    NewWorkOrder,
    Priority,
    TransitionCommand,
    WorkOrder,
    WorkOrderAction,
    WorkOrderState,
)


def _work_order_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "wo-1",
        "reference": "WO-0001",
        "assetId": "asset-1",
        "title": "Replace pump seal",
        "description": "",
        "priority": "high",
        "state": "reported",
        "technicianId": None,
        "reportedAt": "2026-09-24T08:00:00Z",
        "updatedAt": "2026-09-24T08:00:00Z",
    }
    payload.update(overrides)
    return payload


def _error_types(exc: pytest.ExceptionInfo[ValidationError]) -> set[tuple[str, str]]:
    return {(str(err["loc"][0]), err["type"]) for err in exc.value.errors()}


# --- Health ------------------------------------------------------------------


def test_health_status_accepts_contract_value() -> None:
    assert HealthStatus.model_validate({"ok": True}).ok is True


def test_health_status_rejects_values_outside_contract() -> None:
    with pytest.raises(ValidationError):
        HealthStatus.model_validate({"status": "ok"})


# --- WorkOrder.technicianId: required but nullable ----------------------------


def test_work_order_technician_id_accepts_null() -> None:
    work_order = WorkOrder.model_validate(_work_order_payload(technicianId=None))
    assert work_order.technicianId is None


def test_work_order_technician_id_accepts_string() -> None:
    work_order = WorkOrder.model_validate(_work_order_payload(technicianId="tech-1"))
    assert work_order.technicianId == "tech-1"


def test_work_order_technician_id_is_required() -> None:
    payload = _work_order_payload()
    del payload["technicianId"]
    with pytest.raises(ValidationError) as exc:
        WorkOrder.model_validate(payload)
    assert ("technicianId", "missing") in _error_types(exc)


# --- minLength ---------------------------------------------------------------


@pytest.mark.parametrize("field", ["id", "reference", "assetId", "title", "technicianId"])
def test_work_order_rejects_empty_strings(field: str) -> None:
    with pytest.raises(ValidationError) as exc:
        WorkOrder.model_validate(_work_order_payload(**{field: ""}))
    assert (field, "string_too_short") in _error_types(exc)


def test_work_order_description_has_no_min_length() -> None:
    assert WorkOrder.model_validate(_work_order_payload(description="")).description == ""


def test_new_work_order_enforces_min_length() -> None:
    with pytest.raises(ValidationError) as exc:
        NewWorkOrder.model_validate(
            {"assetId": "asset-1", "title": "", "description": "", "priority": "low"}
        )
    assert ("title", "string_too_short") in _error_types(exc)


def test_assignment_command_enforces_min_length() -> None:
    with pytest.raises(ValidationError) as exc:
        AssignmentCommand.model_validate({"technicianId": ""})
    assert ("technicianId", "string_too_short") in _error_types(exc)


# --- Enums are closed --------------------------------------------------------


def test_enum_values_match_contract() -> None:
    assert [s.value for s in WorkOrderState] == [
        "reported",
        "triaged",
        "scheduled",
        "in_progress",
        "completed",
        "cancelled",
    ]
    assert [a.value for a in WorkOrderAction] == [
        "triage",
        "schedule",
        "start",
        "complete",
        "cancel",
    ]
    assert [p.value for p in Priority] == ["low", "medium", "high", "critical"]


@pytest.mark.parametrize(
    ("field", "value"),
    [("state", "on_hold"), ("state", "REPORTED"), ("priority", "urgent")],
)
def test_work_order_rejects_enum_values_outside_contract(field: str, value: str) -> None:
    with pytest.raises(ValidationError) as exc:
        WorkOrder.model_validate(_work_order_payload(**{field: value}))
    assert (field, "enum") in _error_types(exc)


def test_transition_command_rejects_unknown_action() -> None:
    with pytest.raises(ValidationError) as exc:
        TransitionCommand.model_validate({"action": "reopen"})
    assert ("action", "enum") in _error_types(exc)


def test_transition_command_accepts_contract_action() -> None:
    command = TransitionCommand.model_validate({"action": "cancel"})
    assert command.action is WorkOrderAction.cancel
