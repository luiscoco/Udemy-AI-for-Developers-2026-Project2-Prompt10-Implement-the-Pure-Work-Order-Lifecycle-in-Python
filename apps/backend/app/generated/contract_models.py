# GENERATED CODE - DO NOT EDIT. Source: packages/contract/openapi.yaml (datamodel-codegen).
# Regenerate: `npm run contract:generate:py` (root) or `uv run datamodel-codegen` (apps/backend).

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class HealthStatus(BaseModel):
    ok: bool


class WorkOrderState(StrEnum):
    reported = "reported"
    triaged = "triaged"
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class WorkOrderAction(StrEnum):
    triage = "triage"
    schedule = "schedule"
    start = "start"
    complete = "complete"
    cancel = "cancel"


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Asset(BaseModel):
    id: Annotated[str, Field(min_length=1)]
    tag: Annotated[
        str,
        Field(
            description="Human-readable asset tag (e.g. a plate or inventory code).", min_length=1
        ),
    ]
    name: Annotated[str, Field(min_length=1)]
    location: Annotated[str, Field(min_length=1)]


class Technician(BaseModel):
    id: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    specialty: Annotated[str, Field(min_length=1)]


class WorkOrder(BaseModel):
    id: Annotated[str, Field(min_length=1)]
    reference: Annotated[
        str,
        Field(
            description="Human-readable work order reference, assigned by the server.", min_length=1
        ),
    ]
    assetId: Annotated[str, Field(min_length=1)]
    title: Annotated[str, Field(min_length=1)]
    description: str
    priority: Priority
    state: WorkOrderState
    technicianId: Annotated[
        str | None,
        Field(
            description="Assigned technician, or null while unassigned. Always present.",
            min_length=1,
        ),
    ]
    reportedAt: AwareDatetime
    updatedAt: AwareDatetime


class NewWorkOrder(BaseModel):
    assetId: Annotated[str, Field(min_length=1)]
    title: Annotated[str, Field(min_length=1)]
    description: str
    priority: Priority


class TransitionCommand(BaseModel):
    action: WorkOrderAction


class AssignmentCommand(BaseModel):
    technicianId: Annotated[str, Field(min_length=1)]


class ByState(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    reported: Annotated[int, Field(ge=0)]
    triaged: Annotated[int, Field(ge=0)]
    scheduled: Annotated[int, Field(ge=0)]
    in_progress: Annotated[int, Field(ge=0)]
    completed: Annotated[int, Field(ge=0)]
    cancelled: Annotated[int, Field(ge=0)]


class DashboardSummary(BaseModel):
    totalOpen: Annotated[
        int, Field(description="Work orders not in a final state (completed or cancelled).", ge=0)
    ]
    criticalOpen: Annotated[
        int, Field(description="Open work orders with priority `critical`.", ge=0)
    ]
    unassigned: Annotated[
        int, Field(description="Open work orders with no technician assigned.", ge=0)
    ]
    byState: Annotated[
        ByState, Field(description="Count of work orders per state. Every state is always present.")
    ]


class ApiError(BaseModel):
    message: Annotated[str, Field(min_length=1)]
    details: Annotated[
        dict[str, Any] | None,
        Field(description="Optional structured context about the error (e.g. field errors)."),
    ] = None
