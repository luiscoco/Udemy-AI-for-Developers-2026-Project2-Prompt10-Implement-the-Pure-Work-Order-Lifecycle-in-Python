// Public entry point of @equipment-maintenance-hub/contract.
//
// Every alias points into the generated `components['schemas']` map, so shapes are
// defined only in openapi.yaml. Never redeclare a shape here: change the contract and
// run `npm run contract:generate:ts`.
import type { components } from './types.gen';

export type WorkOrderState = components['schemas']['WorkOrderState'];
export type WorkOrderAction = components['schemas']['WorkOrderAction'];
export type Priority = components['schemas']['Priority'];
export type Asset = components['schemas']['Asset'];
export type Technician = components['schemas']['Technician'];
export type WorkOrder = components['schemas']['WorkOrder'];
export type NewWorkOrder = components['schemas']['NewWorkOrder'];
export type TransitionCommand = components['schemas']['TransitionCommand'];
export type AssignmentCommand = components['schemas']['AssignmentCommand'];
export type DashboardSummary = components['schemas']['DashboardSummary'];
export type ApiError = components['schemas']['ApiError'];

export type { components, operations, paths } from './types.gen';

// --- Runtime enum values -------------------------------------------------------
//
// openapi-typescript emits unions only, so the values are listed here for runtime use
// (dropdowns, guards, iteration). The type checker keeps them in sync with the contract:
//   - `const Values extends readonly Union[]`: every listed value is assignable to the
//     generated union (a value removed or renamed in openapi.yaml fails to compile);
//   - `{ missing: ... }`: every union member is listed (a value added in openapi.yaml
//     fails to compile and the error names the missing member).

type Missing<Union, Values extends readonly unknown[]> = Exclude<Union, Values[number]>;

/** Identity at runtime; compile-time check that `values` lists exactly the members of `Union`. */
const enumValues =
  <Union extends string>() =>
  <const Values extends readonly Union[]>(
    values: Values &
      ([Missing<Union, Values>] extends [never]
        ? unknown
        : { readonly missing: Missing<Union, Values> }),
  ): Values =>
    Object.freeze(values);

export const STATES = enumValues<WorkOrderState>()([
  'reported',
  'triaged',
  'scheduled',
  'in_progress',
  'completed',
  'cancelled',
]);

export const ACTIONS = enumValues<WorkOrderAction>()([
  'triage',
  'schedule',
  'start',
  'complete',
  'cancel',
]);

export const PRIORITIES = enumValues<Priority>()(['low', 'medium', 'high', 'critical']);
