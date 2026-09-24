"""Work order lifecycle: the state machine behind ``TransitionCommand``.

Pure domain logic. States and actions come from the OpenAPI contract via ``app.contracts``;
this module only decides which action moves which state where. It must not import FastAPI,
touch files or the database, or raise HTTP errors: callers map ``TransitionFailure`` to
their own error responses.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal

from app.contracts import ACTIONS, WorkOrderAction, WorkOrderState

type TransitionFailureReason = Literal["final_state", "action_not_allowed"]

_TRANSITIONS: Final[
    MappingProxyType[WorkOrderState, MappingProxyType[WorkOrderAction, WorkOrderState]]
] = MappingProxyType(
    {
        WorkOrderState.reported: MappingProxyType({WorkOrderAction.triage: WorkOrderState.triaged}),
        WorkOrderState.triaged: MappingProxyType(
            {
                WorkOrderAction.schedule: WorkOrderState.scheduled,
                WorkOrderAction.cancel: WorkOrderState.cancelled,
            }
        ),
        WorkOrderState.scheduled: MappingProxyType(
            {
                WorkOrderAction.start: WorkOrderState.in_progress,
                WorkOrderAction.cancel: WorkOrderState.cancelled,
            }
        ),
        WorkOrderState.in_progress: MappingProxyType(
            {WorkOrderAction.complete: WorkOrderState.completed}
        ),
        WorkOrderState.completed: MappingProxyType({}),
        WorkOrderState.cancelled: MappingProxyType({}),
    }
)


@dataclass(frozen=True, slots=True)
class TransitionSuccess:
    """``action`` moved the work order from ``from_state`` to ``to_state``."""

    from_state: WorkOrderState
    action: WorkOrderAction
    to_state: WorkOrderState


@dataclass(frozen=True, slots=True)
class TransitionFailure:
    """``action`` is not valid in ``state``; the work order stays where it was."""

    state: WorkOrderState
    action: WorkOrderAction
    reason: TransitionFailureReason


type TransitionResult = TransitionSuccess | TransitionFailure


def is_final(state: WorkOrderState) -> bool:
    """Return whether no action can move a work order out of ``state``."""
    return not _TRANSITIONS[state]


def allowed_actions(state: WorkOrderState) -> tuple[WorkOrderAction, ...]:
    """Return the actions valid in ``state``, in contract order (empty for final states)."""
    outgoing = _TRANSITIONS[state]
    return tuple(action for action in ACTIONS if action in outgoing)


def transition(state: WorkOrderState, action: WorkOrderAction) -> TransitionResult:
    """Apply ``action`` to ``state`` without side effects."""
    outgoing = _TRANSITIONS[state]
    target = outgoing.get(action)
    if target is None:
        reason: TransitionFailureReason = "final_state" if not outgoing else "action_not_allowed"
        return TransitionFailure(state=state, action=action, reason=reason)
    return TransitionSuccess(from_state=state, action=action, to_state=target)


__all__ = [
    "TransitionFailure",
    "TransitionFailureReason",
    "TransitionResult",
    "TransitionSuccess",
    "allowed_actions",
    "is_final",
    "transition",
]
