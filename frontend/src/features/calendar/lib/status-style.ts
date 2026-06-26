import type { InterviewStatus } from '@/features/interviews/types/interview.types';

interface StatusStyle {
  /** Chip background/text/border classes for calendar event pills. */
  chip: string;
  /** Solid dot/accent colour. */
  dot: string;
}

/**
 * Colour coding for interview status across the calendar. Centralised so the
 * month chips, week cards, agenda rows, and legend stay consistent.
 *  - scheduled  → primary (upcoming)
 *  - completed  → success
 *  - cancelled  → destructive (struck through)
 *  - rescheduled→ warning
 *  - no_show    → muted
 */
export const INTERVIEW_STATUS_STYLE: Record<InterviewStatus, StatusStyle> = {
  scheduled: {
    chip: 'border-primary/20 bg-primary/10 text-primary',
    dot: 'bg-primary',
  },
  completed: {
    chip: 'border-success/20 bg-success/10 text-success',
    dot: 'bg-success',
  },
  cancelled: {
    chip: 'border-destructive/20 bg-destructive/10 text-destructive line-through',
    dot: 'bg-destructive',
  },
  rescheduled: {
    chip: 'border-warning/20 bg-warning/15 text-warning',
    dot: 'bg-warning',
  },
  no_show: {
    chip: 'border-border bg-muted text-muted-foreground',
    dot: 'bg-muted-foreground',
  },
};
