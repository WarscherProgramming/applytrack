import type {
  InterviewStatus,
  InterviewType,
} from './types/interview.types';

/** All interview statuses (also drives the form select + status colours). */
export const INTERVIEW_STATUSES = [
  'scheduled',
  'completed',
  'cancelled',
  'rescheduled',
  'no_show',
] as const;

/** All interview types. */
export const INTERVIEW_TYPES = [
  'phone_screen',
  'technical',
  'behavioral',
  'onsite',
  'final',
  'recruiter_call',
  'hiring_manager',
  'other',
] as const;

// Compile-time guards that the arrays stay in sync with the unions.
const _statusCoverage: readonly InterviewStatus[] = INTERVIEW_STATUSES;
const _typeCoverage: readonly InterviewType[] = INTERVIEW_TYPES;
void _statusCoverage;
void _typeCoverage;
