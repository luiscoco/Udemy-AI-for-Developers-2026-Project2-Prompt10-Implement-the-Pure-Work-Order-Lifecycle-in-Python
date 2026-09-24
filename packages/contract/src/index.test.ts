// Contract smoke tests: the runtime enum arrays expose exactly the contract values.
//
// The type checker already rejects unknown or missing members (see `enumValues` in
// index.ts); these tests guard what it cannot see at runtime, such as duplicates.
import { describe, expect, it } from 'vitest';

import { ACTIONS, PRIORITIES, STATES } from './index';

describe('runtime enum values', () => {
  it('STATES includes all six states', () => {
    expect(STATES).toHaveLength(6);
    expect(STATES).toEqual(
      expect.arrayContaining([
        'reported',
        'triaged',
        'scheduled',
        'in_progress',
        'completed',
        'cancelled',
      ]),
    );
  });

  it('ACTIONS includes all five actions', () => {
    expect(ACTIONS).toHaveLength(5);
    expect(ACTIONS).toEqual(
      expect.arrayContaining(['triage', 'schedule', 'start', 'complete', 'cancel']),
    );
  });

  it('PRIORITIES includes all four priorities', () => {
    expect(PRIORITIES).toHaveLength(4);
    expect(PRIORITIES).toEqual(expect.arrayContaining(['low', 'medium', 'high', 'critical']));
  });

  it.each([
    ['STATES', STATES],
    ['ACTIONS', ACTIONS],
    ['PRIORITIES', PRIORITIES],
  ] as const)('%s contains no duplicates', (_name, values) => {
    expect(new Set(values).size).toBe(values.length);
  });
});
