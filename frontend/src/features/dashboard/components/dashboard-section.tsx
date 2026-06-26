import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

import { EmptyState } from '@/components/common/empty-state';
import { ErrorState } from '@/components/common/error-state';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface DashboardSectionProps {
  title: string;
  icon: LucideIcon;
  /** Right-aligned header slot (e.g. a count badge or "View all" link). */
  headerAction?: ReactNode;
  isLoading?: boolean;
  isError?: boolean;
  error?: unknown;
  onRetry?: () => void;
  /** True when there's no data to show (renders the empty state). */
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyIcon?: LucideIcon;
  /** Skeleton rows shown while loading. */
  skeletonRows?: number;
  children?: ReactNode;
}

/**
 * Shared card shell for the dashboard list sections. Centralises the
 * loading / error / empty branching so each section component only has to
 * render its rows.
 */
export function DashboardSection({
  title,
  icon: Icon,
  headerAction,
  isLoading = false,
  isError = false,
  error,
  onRetry,
  isEmpty = false,
  emptyTitle = 'Nothing here yet',
  emptyDescription,
  emptyIcon,
  skeletonRows = 3,
  children,
}: DashboardSectionProps) {
  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Icon className="h-4 w-4 text-muted-foreground" />
          {title}
        </CardTitle>
        {headerAction}
      </CardHeader>
      <CardContent className="flex-1">
        {isError ? (
          <ErrorState error={error} onRetry={onRetry} className="py-8" />
        ) : isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: skeletonRows }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-9 w-9 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-2/3" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
              </div>
            ))}
          </div>
        ) : isEmpty ? (
          <EmptyState
            icon={emptyIcon ?? Icon}
            title={emptyTitle}
            description={emptyDescription}
            className="border-0 py-8"
          />
        ) : (
          <ul className="divide-y">{children}</ul>
        )}
      </CardContent>
    </Card>
  );
}
