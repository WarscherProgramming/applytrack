import { Bell } from 'lucide-react';

import { useFollowupsToday } from '../hooks/use-dashboard-lists';
import { FollowupSection } from './followup-section';

/** Pending follow-ups due today. */
export function FollowupsToday() {
  const query = useFollowupsToday();
  return (
    <FollowupSection
      title="Due today"
      icon={Bell}
      query={query}
      emptyTitle="Nothing due today"
      emptyDescription="You're all caught up for today."
    />
  );
}
