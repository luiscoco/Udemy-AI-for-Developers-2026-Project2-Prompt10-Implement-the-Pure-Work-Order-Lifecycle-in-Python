"""Contract smoke tests: generated models import and ``app.contracts`` exposes the enums."""

import importlib

import pytest
from pydantic import BaseModel

from app import contracts


def test_generated_models_import() -> None:
    module = importlib.import_module("app.generated.contract_models")
    for name in (
        "Asset",
        "Technician",
        "WorkOrder",
        "NewWorkOrder",
        "TransitionCommand",
        "AssignmentCommand",
        "DashboardSummary",
        "ApiError",
    ):
        assert issubclass(getattr(module, name), BaseModel)


def test_contracts_expose_enum_values() -> None:
    assert set(contracts.STATES) == {
        "reported",
        "triaged",
        "scheduled",
        "in_progress",
        "completed",
        "cancelled",
    }
    assert set(contracts.ACTIONS) == {"triage", "schedule", "start", "complete", "cancel"}
    assert set(contracts.PRIORITIES) == {"low", "medium", "high", "critical"}


@pytest.mark.parametrize("name", ["STATES", "ACTIONS", "PRIORITIES"])
def test_runtime_tuples_have_no_duplicates(name: str) -> None:
    values: tuple[str, ...] = getattr(contracts, name)
    assert len(set(values)) == len(values)
