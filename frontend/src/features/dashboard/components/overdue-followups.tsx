import { AlertTriangle } from 'lucide-react';

import { useOverdueFollowups } from '../hooks/use-dashboard-lists';
import { FollowupSection } from './followup-section';

/** Pending follow-ups whose due date has passed. */
export function OverdueFollowups() {
  const query = useOverdueFollowups();
  return (
    <FollowupSection
      title="Overdue follow-ups"
      icon={AlertTriangle}
      query={query}
      emptyTitle="No overdue follow-ups"
      emptyDescription="Great — nothing is past due."
      emphasiseDate
    />
  );
}
