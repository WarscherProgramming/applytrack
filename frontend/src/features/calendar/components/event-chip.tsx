import { format } from 'date-fns';

import { cn } from '@/lib/utils';

import { INTERVIEW_STATUS_STYLE } from '../lib/status-style';
import type { CalendarEvent } from '../types';

interface EventChipProps {
  event: CalendarEvent;
  onSelect: (event: CalendarEvent) => void;
  /** Compact (month cell) vs. roomier (week column) presentation. */
  variant?: 'compact' | 'full';
}

/** A clickable event pill, colour-coded by status. */
export function EventChip({ event, onSelect, variant = 'compact' }: EventChipProps) {
  const style = INTERVIEW_STATUS_STYLE[event.status];

  return (
    <button
      type="button"
      onClick={() => onSelect(event)}
      title={`${format(event.start, 'h:mm a')} · ${event.title}`}
      className={cn(
        'flex w-full items-center gap-1.5 rounded border px-1.5 py-1 text-left text-xs transition-colors hover:brightness-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        style.chip,
      )}
    >
      <span className="font-medium tabular-nums">{format(event.start, 'h:mm a')}</span>
      <span className="truncate">{event.title}</span>
      {variant === 'full' && event.subtitle ? (
        <span className="truncate opacity-70">· {event.subtitle}</span>
      ) : null}
    </button>
  );
}
