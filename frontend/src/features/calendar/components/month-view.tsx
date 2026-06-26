import {
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  format,
  isSameMonth,
  isToday,
  startOfMonth,
  startOfWeek,
} from 'date-fns';
import { useMemo } from 'react';

import { cn } from '@/lib/utils';

import type { CalendarEvent } from '../types';
import { EventChip } from './event-chip';

interface MonthViewProps {
  currentDate: Date;
  events: CalendarEvent[];
  onSelect: (event: CalendarEvent) => void;
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MAX_VISIBLE = 3;
const dayKey = (d: Date) => format(d, 'yyyy-MM-dd');

/** A traditional month grid; days outside the current month are dimmed. */
export function MonthView({ currentDate, events, onSelect }: MonthViewProps) {
  const days = useMemo(() => {
    const gridStart = startOfWeek(startOfMonth(currentDate));
    const gridEnd = endOfWeek(endOfMonth(currentDate));
    return eachDayOfInterval({ start: gridStart, end: gridEnd });
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
    <div className="overflow-hidden rounded-lg border">
      <div className="grid grid-cols-7 border-b bg-muted/40">
        {WEEKDAYS.map((day) => (
          <div
            key={day}
            className="px-2 py-2 text-center text-xs font-medium uppercase tracking-wide text-muted-foreground"
          >
            {day}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7">
        {days.map((day) => {
          const dayEvents = eventsByDay.get(dayKey(day)) ?? [];
          const inMonth = isSameMonth(day, currentDate);
          const today = isToday(day);
          return (
            <div
              key={day.toISOString()}
              className={cn(
                'min-h-[96px] border-b border-r p-1.5 last:border-r-0 [&:nth-child(7n)]:border-r-0',
                !inMonth && 'bg-muted/30 text-muted-foreground',
              )}
            >
              <div className="mb-1 flex justify-end">
                <span
                  className={cn(
                    'flex h-6 w-6 items-center justify-center rounded-full text-xs',
                    today && 'bg-primary font-semibold text-primary-foreground',
                  )}
                >
                  {format(day, 'd')}
                </span>
              </div>
              <div className="space-y-1">
                {dayEvents.slice(0, MAX_VISIBLE).map((event) => (
                  <EventChip key={event.id} event={event} onSelect={onSelect} />
                ))}
                {dayEvents.length > MAX_VISIBLE ? (
                  <p className="px-1 text-xs text-muted-foreground">
                    +{dayEvents.length - MAX_VISIBLE} more
                  </p>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
