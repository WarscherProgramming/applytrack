import type { UseQueryResult } from '@tanstack/react-query';
import type { LucideIcon } from 'lucide-react';
import { ListChecks } from 'lucide-react';

import { PriorityBadge } from '@/components/common/priority-badge';
import type { FollowUp } from '@/features/followups/types/followup.types';
import type { PaginatedResponse } from '@/types/api';
import { cn } from '@/lib/utils';
import { formatDate, humanizeEnum } from '@/utils/format';

import { DashboardSection } from './dashboard-section';
import { SectionRow } from './section-row';

interface FollowupSectionProps {
  title: string;
  icon: LucideIcon;
  query: UseQueryResult<PaginatedResponse<FollowUp>>;
  emptyTitle: string;
  emptyDescription: string;
  /** Render the due date in a destructive colour (overdue emphasis). */
  emphasiseDate?: boolean;
}

/**
 * Shared renderer for the two follow-up reminder lists (today / overdue).
 * Follow-ups carry their own `title`, so no cross-resource lookup is needed.
 */
export function FollowupSection({
  title,
  icon,
  query,
  emptyTitle,
  emptyDescription,
  emphasiseDate = false,
}: FollowupSectionProps) {
  const followups = query.data?.items ?? [];

  return (
    <DashboardSection
      title={title}
      icon={icon}
      isLoading={query.isLoading}
      isError={query.isError}
      error={query.error}
      onRetry={query.refetch}
      isEmpty={followups.length === 0}
      emptyIcon={ListChecks}
      emptyTitle={emptyTitle}
      emptyDescription={emptyDescription}
    >
      {followups.map((followup) => (
        <SectionRow
          key={followup.id}
          title={followup.title}
          subtitle={humanizeEnum(followup.followup_type)}
          meta={
            <div className="flex flex-col items-end gap-1">
              <PriorityBadge priority={followup.priority} />
              <span
                className={cn(
                  'text-xs text-muted-foreground',
                  emphasiseDate && 'font-medium text-destructive',
                )}
              >
                {formatDate(followup.due_date)}
              </span>
            </div>
          }
        />
      ))}
    </DashboardSection>
  );
}
