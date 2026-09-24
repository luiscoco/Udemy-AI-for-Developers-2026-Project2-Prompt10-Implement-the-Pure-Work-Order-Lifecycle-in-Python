# Sample data (fixtures)

This folder holds the seed data for the Equipment Maintenance Hub. All three files follow the schemas in [`packages/contract/openapi.yaml`](../packages/contract/openapi.yaml), so the backend can load them and return them from the API without changing them.

| File | Contents | Contract schema |
|---|---|---|
| [`assets.json`](assets.json) | 6 assets | `Asset` |
| [`technicians.json`](technicians.json) | 5 technicians | `Technician` |
| [`work-orders.json`](work-orders.json) | 15 work orders | `WorkOrder` |

All names, locations and descriptions are made up. None of them refer to real people, real customers or real (proprietary) equipment.

---

## 1. Assets — `assets.json`

An asset is a piece of equipment that needs maintenance.

```json
{ "id": "asset-001", "tag": "HVAC-01", "name": "Rooftop Air Handling Unit", "location": "Building A - Roof" }
```

| Field | Meaning |
|---|---|
| `id` | Internal key. Work orders point to an asset through `assetId`. |
| `tag` | The code a person sees on the equipment's plate or in the inventory, e.g. `HVAC-01`. |
| `name` | What the equipment is. |
| `location` | Where it is installed. |

The six assets:

| id | tag | name | location |
|---|---|---|---|
| asset-001 | HVAC-01 | Rooftop Air Handling Unit | Building A - Roof |
| asset-002 | PUMP-04 | Chilled Water Circulation Pump | Building A - Plant Room B1 |
| asset-003 | CNC-02 | 5-Axis CNC Milling Center | Workshop 2 - Bay 3 |
| asset-004 | UPS-03 | Server Room UPS 40 kVA | Building B - Server Room |
| asset-005 | LIFT-01 | Freight Elevator | Warehouse - North Core |
| asset-006 | COMP-12 | Rotary Screw Air Compressor | Workshop 1 - Utility Corner |

`id` and `tag` are kept separate on purpose. A tag can change, for example when the equipment is relabelled, but the `id` that work orders use never changes.

---

## 2. Technicians — `technicians.json`

```json
{ "id": "tech-001", "name": "Nora Vance", "specialty": "HVAC" }
```

| Field | Meaning |
|---|---|
| `id` | Internal key. Work orders point to a technician through `technicianId`. |
| `name` | Display name (made up). |
| `specialty` | The technician's trade. It helps a person choose who to assign; the API does not enforce it. |

| id | name | specialty |
|---|---|---|
| tech-001 | Nora Vance | HVAC |
| tech-002 | Tomas Arlen | Electrical |
| tech-003 | Priya Holm | Mechanical |
| tech-004 | Diego Marest | CNC & Automation |
| tech-005 | Lena Okafor-Brandt | Lifts & Hoists |

The assignments in the sample match specialties where they can. For example, the UPS work goes to the electrical technician and the CNC spindle work goes to the CNC technician.

---

## 3. Work orders — `work-orders.json`

A work order is a request to fix or service one asset.

```json
{
  "id": "wo-0009",
  "reference": "WO-2026-0009",
  "assetId": "asset-003",
  "title": "Spindle vibration alarm",
  "description": "Spindle vibration alarm at speeds above 12000 rpm. Machine restricted to low-speed jobs.",
  "priority": "critical",
  "state": "in_progress",
  "technicianId": "tech-004",
  "reportedAt": "2026-09-19T07:50:00Z",
  "updatedAt": "2026-09-23T15:10:00Z"
}
```

| Field | Meaning |
|---|---|
| `id` | Internal key, used in URLs such as `/api/work-orders/wo-0009`. |
| `reference` | The number people use, in the format `WO-2026-NNNN`. |
| `assetId` | The equipment this order is for. It must match an `id` in `assets.json`. |
| `title` / `description` | A short summary and the details. |
| `priority` | One of `low`, `medium`, `high`, `critical`. |
| `state` | Where the order is in its lifecycle (see below). |
| `technicianId` | The assigned technician's `id`, or `null` if nobody is assigned. The field is **always present**, even when it is `null`. |
| `reportedAt` | When the order was created (ISO 8601, UTC). |
| `updatedAt` | When the order last changed. It is never earlier than `reportedAt`. |

### 3.1 Lifecycle

The contract defines these states and the actions that move an order between them:

```
reported --triage--> triaged --schedule--> scheduled --start--> in_progress --complete--> completed
                        |                      |
                        +------cancel----------+--------> cancelled
```

`completed` and `cancelled` are **final** states. Once an order reaches one of them, it cannot be transitioned or reassigned; the API returns `409` if you try.

The sample includes orders in every state, and each order's data is consistent with how it could have reached that state:

| State | Count | Assigned? | Why |
|---|---|---|---|
| reported | 3 | none | `POST /api/work-orders` always creates an order as `reported` with no technician. |
| triaged | 3 | 1 of 3 | Someone has reviewed the problem, but a technician may not be assigned yet. |
| scheduled | 2 | all | The work is planned, so someone is responsible for it. |
| in_progress | 3 | all | Someone is doing the work. |
| completed | 2 | all | The technician who did the work is kept. |
| cancelled | 2 | 1 of 2 | One order was cancelled after it was assigned, and one before. |

### 3.2 Priorities

| low | medium | high | critical |
|---|---|---|---|
| 4 | 5 | 3 | 3 |

### 3.3 Unassigned orders

Five orders that are not in a final state have `"technicianId": null`, on purpose. They let you test the "unassigned" count on the dashboard and the assign action:

```json
{
  "id": "wo-0002",
  "reference": "WO-2026-0002",
  "assetId": "asset-006",
  "title": "Compressor tripping on overload",
  "priority": "critical",
  "state": "reported",
  "technicianId": null,
  "reportedAt": "2026-09-23T06:40:00Z",
  "updatedAt": "2026-09-23T06:40:00Z"
}
```

`wo-0002` is critical, open and has no technician, so it is the order a dispatcher should handle first. For a new order that has not been touched yet, `reportedAt` and `updatedAt` are the same.

---

## 4. Expected dashboard values

If the backend loads these files unchanged, `GET /api/dashboard/summary` should return:

```json
{
  "totalOpen": 11,
  "criticalOpen": 2,
  "unassigned": 5,
  "byState": {
    "reported": 3,
    "triaged": 3,
    "scheduled": 2,
    "in_progress": 3,
    "completed": 2,
    "cancelled": 2
  }
}
```

- **totalOpen = 11.** All 15 orders minus the 2 completed and the 2 cancelled.
- **criticalOpen = 2.** `wo-0002` and `wo-0009`. `wo-0012` is also critical, but it is completed, so it is not counted.
- **unassigned = 5.** `wo-0001`, `wo-0002`, `wo-0003`, `wo-0004`, `wo-0006`. `wo-0015` has no technician either, but it is cancelled, so it is not counted.

You can use these numbers as expected values in backend and frontend tests.

---

## 5. Rules the data follows

1. Every `reference` matches `WO-2026-NNNN`.
2. Every `assetId` matches an asset in `assets.json`.
3. Every `technicianId` is either `null` or matches a technician in `technicians.json`.
4. Some orders that are not in a final state are unassigned on purpose.
5. `reportedAt <= updatedAt` for every order.
6. No real people, customer names or proprietary asset data.

### Checking the rules

This Node.js script checks rules 1, 2, 3 and 5, and prints the counts per state and per priority. Run it from the repository root:

```js
// check-fixtures.cjs  —  run with: node check-fixtures.cjs
const assets = require("./data/assets.json");
const technicians = require("./data/technicians.json");
const workOrders = require("./data/work-orders.json");

// Sets of valid ids, so each reference check is a quick lookup.
const assetIds = new Set(assets.map((a) => a.id));
const techIds = new Set(technicians.map((t) => t.id));

const errors = [];
const byState = {};
const byPriority = {};

for (const wo of workOrders) {
  // Count each order by state and by priority.
  byState[wo.state] = (byState[wo.state] || 0) + 1;
  byPriority[wo.priority] = (byPriority[wo.priority] || 0) + 1;

  // Rule 1: the reference has the form WO-2026-NNNN.
  if (!/^WO-2026-\d{4}$/.test(wo.reference)) errors.push(`${wo.id}: bad reference`);

  // Rule 2: the asset must exist.
  if (!assetIds.has(wo.assetId)) errors.push(`${wo.id}: unknown asset`);

  // Rule 3: the technician is null (unassigned) or must exist.
  if (wo.technicianId !== null && !techIds.has(wo.technicianId))
    errors.push(`${wo.id}: unknown technician`);

  // Rule 5: an order cannot be updated before it was reported.
  if (new Date(wo.reportedAt) > new Date(wo.updatedAt)) errors.push(`${wo.id}: updatedAt < reportedAt`);
}

// Rule 4: count the unassigned orders that are not in a final state.
const FINAL = ["completed", "cancelled"];
const unassignedOpen = workOrders.filter((wo) => !wo.technicianId && !FINAL.includes(wo.state)).length;

console.log({ byState, byPriority, unassignedOpen, errors });
```

Expected output: `errors` is an empty array and `unassignedOpen` is `5`.

How the script works:

- **`new Set(...)`:** builds a set of the valid asset ids and a set of the valid technician ids. Checking whether an id is valid is then a single `has()` call, with no search through the arrays.
- **`wo.technicianId !== null && ...`:** `null` means "unassigned" and is allowed, so the technician check only applies when an id is present.
- **`new Date(...)`:** the dates are ISO 8601 strings, so the script turns them into dates before comparing them. This does not depend on how the strings are formatted.
- **`FINAL`:** matches the contract, where `completed` and `cancelled` are final. The same filter is how the dashboard computes `unassigned`.

---

## 6. Running the app on Windows

Open Windows Terminal (PowerShell) and run these commands from the repository root, the folder that contains `package.json`. The path contains spaces, so put it in quotes:

```powershell
cd "C:\path\to\Prompt9"
npm run setup     # first time only: npm install + uv sync for the backend
npm run dev       # starts the frontend and the backend together; Ctrl+C stops both
```

> **Current status:** the Angular app and the FastAPI server are not scaffolded yet. `npm run dev` prints a `TODO` line for each and exits, and **the API does not load these fixture files yet**. The expected values in section 4 will apply once the backend serves this data.

What you can run today:

```powershell
npm test          # contract and backend tests
npm run verify    # drift check, lint, typecheck, test and build
```

To check the fixtures, save the script from section 5 as `check-fixtures.cjs` in the repository root, then run:

```powershell
node check-fixtures.cjs
```

For requirements and fixes for common Windows problems, see [Running on Windows](../README.md#running-on-windows) in the main README.

---

## 7. Changing the data

- Give each new work order the next free number, e.g. `wo-0016` / `WO-2026-0016`. Never reuse a number.
- Keep the state and the technician consistent with the lifecycle in 3.1. For example, a `reported` order has no technician, and an `in_progress` order has one.
- If you change any counts, update the expected values in section 4 and in any tests that use them.
- Run the check script afterwards.
