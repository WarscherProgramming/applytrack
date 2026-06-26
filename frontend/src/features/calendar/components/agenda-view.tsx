import { format, isToday, parseISO } from 'date-fns';
import { useMemo } from 'react';

import { StatusBadge } from '@/components/common/status-badge';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { humanizeEnum } from '@/utils/format';

import type { CalendarEvent } from '../types';

interface AgendaViewProps {
  events: CalendarEvent[];
  onSelect: (event: CalendarEvent) => void;
}

interface DayGroup {
  key: string;
  date: Date;
  events: CalendarEvent[];
}

/** A chronological, date-grouped list of every interview. */
export function AgendaView({ events, onSelect }: AgendaViewProps) {
  const groups = useMemo<DayGroup[]>(() => {
    const map = new Map<string, DayGroup>();
    // events arrive pre-sorted ascending from the adapter.
    for (const event of events) {
      const key = format(event.start, 'yyyy-MM-dd');
      const group = map.get(key);
      if (group) group.events.push(event);
      else map.set(key, { key, date: parseISO(key), events: [event] });
    }
    return [...map.values()];
  }, [events]);

  return (
    <div className="space-y-6">
      {groups.map((group) => {
        const today = isToday(group.date);
        return (
          <div key={group.key} className="space-y-2">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold">
                {format(group.date, 'EEEE, MMMM d, yyyy')}
              </h3>
              {today ? <Badge>Today</Badge> : null}
            </div>
            <div className="overflow-hidden rounded-lg border">
              {group.events.map((event, idx) => (
                <button
                  key={event.id}
                  type="button"
                  onClick={() => onSelect(event)}
                  className={cn(
                    'flex w-full items-center gap-4 px-4 py-3 text-left transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring',
                    idx > 0 && 'border-t',
                  )}
                >
                  <div className="w-20 shrink-0 text-sm font-medium tabular-nums">
                    {format(event.start, 'h:mm a')}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{event.title}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {event.subtitle ?? 'Unknown company'}
                      {event.data.interview.interview_type
                        ? ` · ${humanizeEnum(event.data.interview.interview_type)}`
                        : ''}
                    </p>
                  </div>
                  <StatusBadge status={event.status} className="shrink-0" />
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
