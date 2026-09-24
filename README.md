# Work order lifecycle

[`apps/backend/app/domain/`](apps/backend/app/domain/) holds pure business rules. Code there
has no FastAPI imports, no file or database access, and never raises `HTTPException`. It
takes values in and returns values out, so it can be tested with plain function calls and
reused from any layer (API routes, scripts, background jobs).

[`work_order_lifecycle.py`](apps/backend/app/domain/work_order_lifecycle.py) is the state
machine that decides which action moves a work order from one state to another.

## The rules

```
reported ──triage──▶ triaged ──schedule──▶ scheduled ──start──▶ in_progress ──complete──▶ completed
                        │                      │
                        └──cancel──┐  ┌──cancel─┘
                                   ▼  ▼
                                cancelled
```

| From          | Action     | To            |
| ------------- | ---------- | ------------- |
| `reported`    | `triage`   | `triaged`     |
| `triaged`     | `schedule` | `scheduled`   |
| `triaged`     | `cancel`   | `cancelled`   |
| `scheduled`   | `start`    | `in_progress` |
| `scheduled`   | `cancel`   | `cancelled`   |
| `in_progress` | `complete` | `completed`   |

`completed` and `cancelled` are **final**: no action leaves them. Any pair not in the table
is rejected.

## Quick usage

```python
from app.contracts import WorkOrderAction, WorkOrderState
from app.domain.work_order_lifecycle import (
    TransitionFailure,
    TransitionSuccess,
    allowed_actions,
    transition,
)

allowed_actions(WorkOrderState.triaged)
# (WorkOrderAction.schedule, WorkOrderAction.cancel)

result = transition(WorkOrderState.reported, WorkOrderAction.triage)
match result:
    case TransitionSuccess(to_state=new_state):
        print(f"moved to {new_state}")  # moved to triaged
    case TransitionFailure(reason=reason):
        print(f"rejected: {reason}")
```

## Code walkthrough

### 1. Imports: states and actions come from the contract

```python
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal

from app.contracts import ACTIONS, WorkOrderAction, WorkOrderState
```

`WorkOrderState` and `WorkOrderAction` are **not** declared here. They are generated from
`packages/contract/openapi.yaml` and re-exported by `app.contracts`, so the backend, the
frontend and this state machine all use the same names. If the contract adds a state, add
it to the table below as well: mypy does not detect a state missing from the table.

Only the standard library and `app.contracts` are imported. This is what keeps the module
free of framework and I/O dependencies.

### 2. Failure reasons as a closed set

```python
type TransitionFailureReason = Literal["final_state", "action_not_allowed"]
```

A `Literal` type lists the only strings allowed as a reason. mypy rejects a typo such as
`"final-state"`, and callers can match on the value safely.

- `"final_state"`: the work order is `completed` or `cancelled`, so nothing can change it.
- `"action_not_allowed"`: the state has exits, but not for this action (for example
  `start` on a `reported` order).

### 3. The transition table

```python
_TRANSITIONS: Final[
    MappingProxyType[WorkOrderState, MappingProxyType[WorkOrderAction, WorkOrderState]]
] = MappingProxyType(
    {
        WorkOrderState.reported: MappingProxyType(
            {WorkOrderAction.triage: WorkOrderState.triaged}
        ),
        WorkOrderState.triaged: MappingProxyType(
            {
                WorkOrderAction.schedule: WorkOrderState.scheduled,
                WorkOrderAction.cancel: WorkOrderState.cancelled,
            }
        ),
        # ... scheduled, in_progress ...
        WorkOrderState.completed: MappingProxyType({}),
        WorkOrderState.cancelled: MappingProxyType({}),
    }
)
```

All the rules live in one place: `state → {action → next state}`. Reading the table is
reading the rules.

- **`MappingProxyType`** is a read-only view of a dict. Code that tries
  `_TRANSITIONS[...] = ...` fails at runtime, so the rules cannot be changed by accident.
- **`Final`** tells mypy that the name `_TRANSITIONS` is never reassigned.
- The leading **underscore** marks it as private. Other modules use the functions below
  instead of reading the table directly.
- Final states map to an **empty** mapping. Every state has an entry, so a lookup never
  raises `KeyError`.

### 4. The result types

```python
@dataclass(frozen=True, slots=True)
class TransitionSuccess:
    from_state: WorkOrderState
    action: WorkOrderAction
    to_state: WorkOrderState


@dataclass(frozen=True, slots=True)
class TransitionFailure:
    state: WorkOrderState
    action: WorkOrderAction
    reason: TransitionFailureReason


type TransitionResult = TransitionSuccess | TransitionFailure
```

`transition()` **returns** a failure instead of raising an exception. That has two benefits:

- The return type `TransitionSuccess | TransitionFailure` forces callers to handle both
  cases, and mypy checks that they do.
- The domain does not decide the HTTP status. An API route can turn a
  `TransitionFailure` into a 409 or 422 with its own `ApiError` body, while a script might
  just log it.

`frozen=True` makes the objects immutable, and `slots=True` keeps them small and blocks
setting attributes that were not declared.

### 5. `is_final`

```python
def is_final(state: WorkOrderState) -> bool:
    return not _TRANSITIONS[state]
```

A state is final when its outgoing mapping is empty. `not {}` is `True`, so this returns
`True` for `completed` and `cancelled`.

### 6. `allowed_actions`

```python
def allowed_actions(state: WorkOrderState) -> tuple[WorkOrderAction, ...]:
    outgoing = _TRANSITIONS[state]
    return tuple(action for action in ACTIONS if action in outgoing)
```

It loops over `ACTIONS` (every action in the order the contract declares them) and keeps
those valid in `state`. Walking `ACTIONS` rather than the table's own keys means the order
is always the contract's order, which is stable for UI buttons and for tests. It returns a
`tuple`, so callers cannot modify the result. Final states return `()`.

| State         | `allowed_actions(state)` |
| ------------- | ------------------------ |
| `reported`    | `(triage,)`              |
| `triaged`     | `(schedule, cancel)`     |
| `scheduled`   | `(start, cancel)`        |
| `in_progress` | `(complete,)`            |
| `completed`   | `()`                     |
| `cancelled`   | `()`                     |

### 7. `transition`

```python
def transition(state: WorkOrderState, action: WorkOrderAction) -> TransitionResult:
    outgoing = _TRANSITIONS[state]
    target = outgoing.get(action)
    if target is None:
        reason: TransitionFailureReason = "final_state" if not outgoing else "action_not_allowed"
        return TransitionFailure(state=state, action=action, reason=reason)
    return TransitionSuccess(from_state=state, action=action, to_state=target)
```

Step by step:

1. Look up the exits of the current state.
2. `.get(action)` returns the next state, or `None` if the action is not an exit.
3. If there is no exit, choose the reason: an empty `outgoing` means a final state,
   otherwise the action simply is not valid here.
4. Otherwise, return a success with the new state.

The function has no side effects. It does not change a work order; it only tells the caller
what the new state would be. Saving it is the job of another layer.

Examples:

```python
transition(WorkOrderState.scheduled, WorkOrderAction.start)
# TransitionSuccess(from_state=scheduled, action=start, to_state=in_progress)

transition(WorkOrderState.reported, WorkOrderAction.start)
# TransitionFailure(state=reported, action=start, reason='action_not_allowed')

transition(WorkOrderState.completed, WorkOrderAction.cancel)
# TransitionFailure(state=completed, action=cancel, reason='final_state')
```

(Output shortened. Python prints each enum in full, for example
`<WorkOrderState.scheduled: 'scheduled'>`.)

## Running the app in the Windows terminal

> **Current status:** the Angular frontend is not scaffolded yet and the FastAPI server is
> not written yet. `npm run dev` starts both processes, but each one only prints a `TODO`
> message and exits. There is no page to open in the browser yet. To see working code today,
> run the lifecycle demo in the next section.

These commands are for **PowerShell** (the default shell in Windows Terminal) and run from
the repository root.

### Requirements

| Tool | Version | Check with |
| --- | --- | --- |
| [Node.js](https://nodejs.org/) | 22 or later | `node --version` |
| npm | comes with Node.js | `npm --version` |
| [uv](https://docs.astral.sh/uv/) (Python manager) | any recent | `uv --version` |

uv downloads the Python version the backend needs (3.13), so a separate Python install is not
required.

### 1. Open the project folder

```powershell
cd "C:\path\to\Prompt10"
```

Replace `C:\path\to\Prompt10` with your own folder. Keep the quotes: the path contains spaces.

### 2. Install everything (first time only)

```powershell
npm run setup
```

This runs `npm install` for the frontend and contract packages, then `uv sync` for the
backend. If uv's progress lines appear in red, that is normal: uv writes progress to stderr.

### 3. Start the app

```powershell
npm run dev
```

This uses `concurrently` to start the frontend and backend side by side, with each line
prefixed by `[frontend]` or `[backend]`. Today the output is:

```
[backend] TODO: start FastAPI dev server
[backend] npm run backend:dev exited with code 0
[frontend] "TODO: ng serve (Angular 22 not scaffolded yet)"
[frontend] npm run frontend:dev exited with code 0
```

Once the real servers exist, this command will keep running; stop it with `Ctrl+C`.

To start only one side:

```powershell
npm run frontend:dev
npm run backend:dev
```

### 4. Check that everything works

```powershell
npm run verify
```

This checks that the generated contract models are up to date, then runs lint, type checks,
tests and the build for every package. It stops at the first failure. A clean run ends with
`Successfully built ... .whl`.

## Running the lifecycle demo in the Windows terminal

There is no web server yet: the root `npm run backend:dev` script is still a placeholder.
This module is plain Python, so you can call it directly. You need
[uv](https://docs.astral.sh/uv/) installed.

The commands below are for **PowerShell** (the default shell in Windows Terminal).

### 1. Go to the backend folder and install dependencies

```powershell
cd "C:\path\to\Prompt10\apps\backend"
uv sync
```

Replace `C:\path\to\Prompt10` with the folder where you cloned the project. The quotes are
needed because the path contains spaces. `uv sync` creates the virtual environment the first
time; after that it is quick.

### 2. Try a single transition

```powershell
uv run python -c "from app.domain.work_order_lifecycle import transition; print(transition('triaged', 'cancel'))"
```

Expected output:

```
TransitionSuccess(from_state='triaged', action='cancel', to_state=<WorkOrderState.cancelled: 'cancelled'>)
```

`uv run` runs Python inside the project's virtual environment, so `app` can be imported.
Plain strings like `'triaged'` work because `WorkOrderState` and `WorkOrderAction` are
`StrEnum`s, but inside the application prefer the enum members.

### 3. Run the full demo

Paste this whole block into PowerShell. It sends the script to Python through a
here-string (`@' ... '@`), so there is no temporary file to create:

```powershell
@'
from app.contracts import STATES, WorkOrderAction, WorkOrderState
from app.domain.work_order_lifecycle import allowed_actions, transition

for state in STATES:
    print(f"{state:<12} -> {[a.value for a in allowed_actions(state)]}")

print(transition(WorkOrderState.scheduled, WorkOrderAction.start))
print(transition(WorkOrderState.reported, WorkOrderAction.start))
print(transition(WorkOrderState.completed, WorkOrderAction.cancel))
'@ | uv run python -
```

The closing `'@` must be at the very start of its line. The `-` after `python` tells Python
to read the script from the pipe. Expected output:

```
reported     -> ['triage']
triaged      -> ['schedule', 'cancel']
scheduled    -> ['start', 'cancel']
in_progress  -> ['complete']
completed    -> []
cancelled    -> []
TransitionSuccess(from_state=<WorkOrderState.scheduled: 'scheduled'>, action=<WorkOrderAction.start: 'start'>, to_state=<WorkOrderState.in_progress: 'in_progress'>)
TransitionFailure(state=<WorkOrderState.reported: 'reported'>, action=<WorkOrderAction.start: 'start'>, reason='action_not_allowed')
TransitionFailure(state=<WorkOrderState.completed: 'completed'>, action=<WorkOrderAction.cancel: 'cancel'>, reason='final_state')
```

#### What the demo does, line by line

```python
from app.contracts import STATES, WorkOrderAction, WorkOrderState
from app.domain.work_order_lifecycle import allowed_actions, transition
```

Imports the contract types and the two public functions. `STATES` is a tuple of every
`WorkOrderState` in contract order, so the loop below covers all six states.

```python
for state in STATES:
    print(f"{state:<12} -> {[a.value for a in allowed_actions(state)]}")
```

For each state, asks the lifecycle which actions are valid.

- `{state:<12}` prints the state name padded to 12 characters, so the arrows line up.
- `[a.value for a in ...]` turns each `WorkOrderAction` into its plain string (`'triage'`),
  which is easier to read than the full enum.
- The last two lines print `[]`: `completed` and `cancelled` are final.

```python
print(transition(WorkOrderState.scheduled, WorkOrderAction.start))
```

A valid move. The result is a `TransitionSuccess` with `to_state=in_progress`.

```python
print(transition(WorkOrderState.reported, WorkOrderAction.start))
```

An invalid move from a state that still has exits (`reported` only allows `triage`). The
result is a `TransitionFailure` with `reason='action_not_allowed'`.

```python
print(transition(WorkOrderState.completed, WorkOrderAction.cancel))
```

Any action on a final state. The result is a `TransitionFailure` with
`reason='final_state'`. Neither failure raises an exception: the caller decides what to do.

### 4. Check the code

From the same `apps\backend` folder:

```powershell
uv run ruff check
uv run mypy
uv run pytest
```

Or from the repository root (`Prompt10`), with npm:

```powershell
npm run backend:lint
npm run backend:typecheck
npm run backend:test
```

## Changing the rules

1. If a state or action is new, add it to `packages/contract/openapi.yaml` and run
   `npm run contract:generate:py`.
2. Edit only `_TRANSITIONS` in `apps/backend/app/domain/work_order_lifecycle.py`.
   `allowed_actions`, `transition` and `is_final` all read from it.
3. Run `uv run ruff check`, `uv run mypy` and `uv run pytest` from `apps/backend`.
