import { ChevronLeft, ChevronRight } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

import type { CalendarView } from '../types';

interface CalendarToolbarProps {
  view: CalendarView;
  onViewChange: (view: CalendarView) => void;
  /** Heading for the current range (e.g. "June 2026"). Hidden for agenda. */
  label: string;
  /** Date navigation — only shown for month/week. */
  onPrev: () => void;
  onNext: () => void;
  onToday: () => void;
}

const VIEWS: { value: CalendarView; label: string }[] = [
  { value: 'month', label: 'Month' },
  { value: 'week', label: 'Week' },
  { value: 'agenda', label: 'Agenda' },
];

/** Top bar: date navigation (month/week) + the view switcher. */
export function CalendarToolbar({
  view,
  onViewChange,
  label,
  onPrev,
  onNext,
  onToday,
}: CalendarToolbarProps) {
  const showNav = view !== 'agenda';

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        {showNav ? (
          <>
            <div className="flex items-center gap-1">
              <Button variant="outline" size="icon" onClick={onPrev} aria-label="Previous">
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" onClick={onNext} aria-label="Next">
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
            <Button variant="outline" size="sm" onClick={onToday}>
              Today
            </Button>
            <h2 className="text-lg font-semibold">{label}</h2>
          </>
        ) : (
          <h2 className="text-lg font-semibold">Agenda</h2>
        )}
      </div>

      <div
        role="tablist"
        aria-label="Calendar view"
        className="inline-flex rounded-lg border bg-muted/40 p-1"
      >
        {VIEWS.map(({ value, label: viewLabel }) => (
          <button
            key={value}
            role="tab"
            aria-selected={view === value}
            type="button"
            onClick={() => onViewChange(value)}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              view === value
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {viewLabel}
          </button>
        ))}
      </div>
    </div>
  );
}
