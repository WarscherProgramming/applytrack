import { cn } from '@/lib/utils';

import type { GenerationHistoryEntry } from '../types';

interface GenerationHistoryProps {
  entries: GenerationHistoryEntry[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

/**
 * Session-scoped list of generations produced on this page. Saved letters live
 * in the Cover Letter Library (with full version history); this is a quick way
 * to revisit drafts generated during the current session.
 */
export function GenerationHistory({
  entries,
  selectedId,
  onSelect,
}: GenerationHistoryProps) {
  if (entries.length === 0) {
    return (
      <p className="rounded-lg border border-dashed p-4 text-center text-sm text-muted-foreground">
        Generations from this session will appear here.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {entries.map((entry) => (
        <li key={entry.id}>
          <button
            type="button"
            onClick={() => onSelect(entry.id)}
            className={cn(
              'w-full rounded-lg border p-3 text-left transition-colors hover:bg-accent',
              selectedId === entry.id && 'border-primary bg-primary/5',
            )}
          >
            <p className="truncate text-sm font-medium">
              {entry.company_name} · {entry.job_title}
            </p>
            <p className="truncate text-xs text-muted-foreground">
              {entry.resume_name}
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground/70">
              {new Date(entry.createdAt).toLocaleTimeString()} ·{' '}
              {entry.usage.total_tokens.toLocaleString()} tokens
            </p>
          </button>
        </li>
      ))}
    </ul>
  );
}
