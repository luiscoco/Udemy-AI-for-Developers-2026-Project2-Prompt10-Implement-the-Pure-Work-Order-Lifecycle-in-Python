"""Public entry point for the OpenAPI contract on the backend.

Import contract models from here, not from ``app.generated``. Every model is re-exported
unchanged from the generated module, so shapes are defined only in
``packages/contract/openapi.yaml``. Never redeclare a model here: change the contract and
run ``npm run contract:generate:py``.

``STATES``, ``ACTIONS`` and ``PRIORITIES`` are immutable tuples built from the generated
enums, so they cannot drift from the contract. They mirror the TypeScript constants of the
same names in ``@equipment-maintenance-hub/contract`` and keep the contract's order.
"""

from typing import Final

from app.generated.contract_models import (
    ApiError,
    Asset,
    AssignmentCommand,
    ByState,
    DashboardSummary,
    HealthStatus,
    NewWorkOrder,
    Priority,
    Technician,
    TransitionCommand,
    WorkOrder,
    WorkOrderAction,
    WorkOrderState,
)

STATES: Final[tuple[WorkOrderState, ...]] = tuple(WorkOrderState)
ACTIONS: Final[tuple[WorkOrderAction, ...]] = tuple(WorkOrderAction)
PRIORITIES: Final[tuple[Priority, ...]] = tuple(Priority)

__all__ = [
    "ACTIONS",
    "PRIORITIES",
    "STATES",
    "ApiError",
    "Asset",
    "AssignmentCommand",
    "ByState",
    "DashboardSummary",
    "HealthStatus",
    "NewWorkOrder",
    "Priority",
    "Technician",
    "TransitionCommand",
    "WorkOrder",
    "WorkOrderAction",
    "WorkOrderState",
]
