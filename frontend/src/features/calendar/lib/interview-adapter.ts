import { addMinutes, parseISO } from 'date-fns';

import type { Application } from '@/features/applications/types/application.types';
import type { Interview } from '@/features/interviews/types/interview.types';

import type { CalendarEvent, EnrichedInterview } from '../types';

interface Lookups {
  companyById: Map<string, string>;
  applicationById: Map<string, Application>;
  recruiterById: Map<string, string>;
}

/** Attach the human-readable names an interview references by id. */
export function enrichInterview(
  interview: Interview,
  { companyById, applicationById, recruiterById }: Lookups,
): EnrichedInterview {
  const application = applicationById.get(interview.application_id);
  return {
    interview,
    jobTitle: application?.job_title,
    companyName: application ? companyById.get(application.company_id) : undefined,
    recruiterName: interview.recruiter_id
      ? recruiterById.get(interview.recruiter_id)
      : undefined,
  };
}

/**
 * The single adapter from an interview to the generic CalendarEvent the views
 * render. Adding Google/Outlook later means writing a sibling adapter that
 * produces CalendarEvents — the views never change.
 */
export function interviewToEvent(enriched: EnrichedInterview): CalendarEvent {
  const start = parseISO(enriched.interview.scheduled_at);
  return {
    id: enriched.interview.id,
    source: 'interview',
    title: enriched.jobTitle ?? 'Interview',
    subtitle: enriched.companyName,
    start,
    end: addMinutes(start, enriched.interview.duration_minutes),
    status: enriched.interview.status,
    data: enriched,
  };
}

/** Map a list of interviews into sorted CalendarEvents. */
export function interviewsToEvents(
  interviews: Interview[],
  lookups: Lookups,
): CalendarEvent[] {
  return interviews
    .map((interview) => interviewToEvent(enrichInterview(interview, lookups)))
    .sort((a, b) => a.start.getTime() - b.start.getTime());
}
