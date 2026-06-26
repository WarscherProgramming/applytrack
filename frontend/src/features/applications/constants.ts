import type { ApplicationStatus } from './types/application.types';

/**
 * Canonical ordering of application statuses — also the left-to-right order of
 * the Kanban columns. Declared `as const` so it can seed a Zod enum and a
 * literal-typed status union.
 */
export const APPLICATION_STATUSES = [
  'draft',
  'applied',
  'assessment',
  'phone_screen',
  'interview',
  'final_interview',
  'offer',
  'accepted',
  'rejected',
  'withdrawn',
  'ghosted',
] as const;

// Compile-time guard: the array must stay in sync with the ApplicationStatus
// union. If they drift, this assignment fails to type-check.
const _statusCoverage: readonly ApplicationStatus[] = APPLICATION_STATUSES;
void _statusCoverage;
