import type {
  Interview,
  InterviewStatus,
} from '@/features/interviews/types/interview.types';

/** The three calendar layouts the user can switch between. */
export type CalendarView = 'month' | 'week' | 'agenda';

/**
 * Where an event came from. Today only interviews exist, but the calendar is
 * designed so Google/Outlook events can be added later by writing another
 * adapter (event source → CalendarEvent) without touching the views.
 */
export type CalendarSource = 'interview' | 'google' | 'outlook';

/** An interview enriched with the names the calendar needs to display. */
export interface EnrichedInterview {
  interview: Interview;
  companyName?: string;
  jobTitle?: string;
  recruiterName?: string;
}

/**
 * The generic shape every calendar view renders. Views only read the
 * presentation fields (title/subtitle/start/end/status); `source` + `data`
 * let the page route a click to the right detail handler. When new sources are
 * added, widen `data` to a discriminated union on `source` — the views stay
 * unchanged.
 */
export interface CalendarEvent {
  id: string;
  source: CalendarSource;
  title: string;
  subtitle?: string;
  start: Date;
  end: Date;
  /** Drives colour coding. Reused from interview status for now. */
  status: InterviewStatus;
  data: EnrichedInterview;
}
