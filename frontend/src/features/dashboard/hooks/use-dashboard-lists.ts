import { useQuery } from '@tanstack/react-query';

import { followupsApi } from '@/features/followups/api/followups.api';
import { interviewsApi } from '@/features/interviews/api/interviews.api';

// Each dashboard list shows a short preview; "View all" (a future milestone)
// will link to the full resource page.
const PREVIEW_LIMIT = 5;

/** Next scheduled interviews, soonest first (backend sorts by scheduled_at asc). */
export function useUpcomingInterviews() {
  return useQuery({
    queryKey: ['dashboard', 'upcoming-interviews'],
    queryFn: () =>
      interviewsApi.list({ status: 'scheduled', skip: 0, limit: PREVIEW_LIMIT }),
  });
}

/** Pending follow-ups due today. */
export function useFollowupsToday() {
  return useQuery({
    queryKey: ['dashboard', 'followups-today'],
    queryFn: () => followupsApi.listToday({ skip: 0, limit: PREVIEW_LIMIT }),
  });
}

/** Pending follow-ups whose due date has passed. */
export function useOverdueFollowups() {
  return useQuery({
    queryKey: ['dashboard', 'followups-overdue'],
    queryFn: () => followupsApi.listOverdue({ skip: 0, limit: PREVIEW_LIMIT }),
  });
}
