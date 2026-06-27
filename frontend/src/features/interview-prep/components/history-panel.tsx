import { Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { formatDate } from '@/utils/format';

import type { InterviewPrepListItem } from '../types';

interface HistoryPanelProps {
  items: InterviewPrepListItem[];
  selectedId: string | null;
  isLoading: boolean;
  onSelect: (id: string) => void;
  onDelete: (item: InterviewPrepListItem) => void;
}

export function HistoryPanel({
  items,
  selectedId,
  isLoading,
  onSelect,
  onDelete,
}: HistoryPanelProps) {
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
        No saved packages yet. Generate one to start your history.
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
              'group flex cursor-pointer items-start gap-2 rounded-lg border p-3 transition-colors hover:bg-accent',
              selectedId === item.id && 'border-primary bg-primary/5',
            )}
          >
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">
                {item.company_name} · {item.job_title}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {item.interview_type ?? 'General'}
                {item.interview_round ? ` · ${item.interview_round}` : ''}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground/70">
                {formatDate(item.created_at)}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 hover:text-destructive"
              aria-label={`Delete prep for ${item.company_name}`}
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
