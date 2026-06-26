import type { LucideIcon } from 'lucide-react';

import { EmptyState } from '@/components/common/empty-state';
import { PageHeader } from '@/components/common/page-header';

interface PlaceholderPageProps {
  title: string;
  description: string;
  icon: LucideIcon;
}

/**
 * Shared scaffold for feature pages not yet implemented in this milestone
 * (Applications, Recruiters, Interviews, Follow-ups). Keeps routing and the
 * shell complete while signalling that CRUD lands in a later milestone.
 */
export function PlaceholderPage({
  title,
  description,
  icon,
}: PlaceholderPageProps) {
  return (
    <div className="space-y-6">
      <PageHeader title={title} description={description} />
      <EmptyState
        icon={icon}
        title={`${title} are coming soon`}
        description="This section is part of a later milestone. The backend API is ready; the UI will be built next."
      />
    </div>
  );
}
