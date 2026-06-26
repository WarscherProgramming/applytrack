import {
  eachDayOfInterval,
  endOfWeek,
  format,
  isToday,
  startOfWeek,
} from 'date-fns';
import { useMemo } from 'react';

import { cn } from '@/lib/utils';

import type { CalendarEvent } from '../types';
import { EventChip } from './event-chip';

interface WeekViewProps {
  currentDate: Date;
  events: CalendarEvent[];
  onSelect: (event: CalendarEvent) => void;
}

const dayKey = (d: Date) => format(d, 'yyyy-MM-dd');

/**
 * Seven day-columns for the current week, each listing its interviews in time
 * order. Stacks to a single column on small screens.
 */
export function WeekView({ currentDate, events, onSelect }: WeekViewProps) {
  const days = useMemo(() => {
    const start = startOfWeek(currentDate);
    return eachDayOfInterval({ start, end: endOfWeek(currentDate) });
  }, [currentDate]);

  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    for (const event of events) {
      const key = dayKey(event.start);
      const list = map.get(key);
      if (list) list.push(event);
      else map.set(key, [event]);
    }
    return map;
  }, [events]);

  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-7">
      {days.map((day) => {
        const dayEvents = eventsByDay.get(dayKey(day)) ?? [];
        const today = isToday(day);
        return (
          <div
            key={day.toISOString()}
            className={cn(
              'flex flex-col rounded-lg border',
              today && 'border-primary/40 ring-1 ring-primary/20',
            )}
          >
            <div
              className={cn(
                'border-b px-2 py-2 text-center',
                today && 'bg-primary/5',
              )}
            >
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                {format(day, 'EEE')}
              </p>
              <p
                className={cn(
                  'text-sm font-semibold',
                  today && 'text-primary',
                )}
              >
                {format(day, 'd')}
              </p>
            </div>
            <div className="flex-1 space-y-1.5 p-1.5">
              {dayEvents.length === 0 ? (
                <p className="py-3 text-center text-xs text-muted-foreground/60">
                  —
                </p>
              ) : (
                dayEvents.map((event) => (
                  <EventChip
                    key={event.id}
                    event={event}
                    onSelect={onSelect}
                    variant="full"
                  />
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
