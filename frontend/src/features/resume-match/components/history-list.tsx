import { Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { formatDate } from '@/utils/format';

import { scoreColorClass } from '../lib';
import type { ResumeMatchListItem } from '../types';

interface HistoryListProps {
  items: ResumeMatchListItem[];
  selectedId: string | null;
  isLoading: boolean;
  onSelect: (id: string) => void;
  onDelete: (item: ResumeMatchListItem) => void;
}

export function HistoryList({
  items,
  selectedId,
  isLoading,
  onSelect,
  onDelete,
}: HistoryListProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <p className="rounded-lg border border-dashed p-4 text-center text-sm text-muted-foreground">
        No analyses yet. Run your first match to see it here.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li key={item.id}>
          <div
            role="button"
            tabIndex={0}
            onClick={() => onSelect(item.id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelect(item.id);
              }
            }}
            className={cn(
              'group flex w-full cursor-pointer items-start gap-3 rounded-lg border p-3 text-left transition-colors hover:bg-accent',
              selectedId === item.id && 'border-primary bg-primary/5',
            )}
          >
            <span
              className={cn(
                'flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-muted text-sm font-bold tabular-nums',
                scoreColorClass(item.overall_match_score),
              )}
            >
              {item.overall_match_score}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{item.resume_name}</p>
              <p className="truncate text-xs text-muted-foreground">
                {item.job_description_preview}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground/70">
                {formatDate(item.created_at)}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 hover:text-destructive"
              aria-label={`Delete analysis for ${item.resume_name}`}
              onClick={(e) => {
                e.stopPropagation();
                onDelete(item);
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </li>
      ))}
    </ul>
  );
}
