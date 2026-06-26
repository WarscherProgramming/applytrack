import type { ReactNode } from 'react';

import { cn } from '@/lib/utils';

interface SectionRowProps {
  /** Primary line (e.g. job title or follow-up title). */
  title: ReactNode;
  /** Secondary muted line (e.g. company, type). */
  subtitle?: ReactNode;
  /** Right-aligned content (e.g. a badge or date). */
  meta?: ReactNode;
  /** Optional leading visual (icon chip / avatar). */
  leading?: ReactNode;
  className?: string;
}

/** One consistent row inside a dashboard list section. */
export function SectionRow({
  title,
  subtitle,
  meta,
  leading,
  className,
}: SectionRowProps) {
  return (
    <li className={cn('flex items-center gap-3 py-3 first:pt-0 last:pb-0', className)}>
      {leading}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{title}</p>
        {subtitle ? (
          <p className="truncate text-xs text-muted-foreground">{subtitle}</p>
        ) : null}
      </div>
      {meta ? <div className="shrink-0 text-right">{meta}</div> : null}
    </li>
  );
}
