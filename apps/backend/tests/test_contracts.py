"""Tests for ``app.contracts``: re-exported models and the runtime enum tuples."""

from enum import StrEnum

import pytest

from app import contracts
from app.generated import contract_models


def test_models_are_re_exported_unchanged() -> None:
    for name in contracts.__all__:
        if name.isupper():
            continue
        assert getattr(contracts, name) is getattr(contract_models, name)


def test_every_generated_model_is_re_exported() -> None:
    generated = {
        name
        for name, value in vars(contract_models).items()
        if isinstance(value, type) and value.__module__ == contract_models.__name__
    }
    assert generated <= set(contracts.__all__)


@pytest.mark.parametrize(
    ("values", "enum"),
    [
        (contracts.STATES, contracts.WorkOrderState),
        (contracts.ACTIONS, contracts.WorkOrderAction),
        (contracts.PRIORITIES, contracts.Priority),
    ],
)
def test_tuples_match_generated_enums_in_contract_order(
    values: object, enum: type[StrEnum]
) -> None:
    assert isinstance(values, tuple)
    assert values == tuple(enum)


def test_tuples_hold_the_contract_strings() -> None:
    assert contracts.STATES == (
        "reported",
        "triaged",
        "scheduled",
        "in_progress",
        "completed",
        "cancelled",
    )
    assert contracts.ACTIONS == ("triage", "schedule", "start", "complete", "cancel")
    assert contracts.PRIORITIES == ("low", "medium", "high", "critical")
