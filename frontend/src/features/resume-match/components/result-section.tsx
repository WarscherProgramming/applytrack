import type { LucideIcon } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface ResultSectionProps {
  icon: LucideIcon;
  title: string;
  items: string[];
  iconClassName?: string;
  /** Render items as inline pills (for keywords) instead of a bulleted list. */
  variant?: 'list' | 'tags';
}

/** One titled block of the analysis (strengths, weaknesses, etc.). */
export function ResultSection({
  icon: Icon,
  title,
  items,
  iconClassName,
  variant = 'list',
}: ResultSectionProps) {
  if (items.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold">
        <Icon className={cn('h-4 w-4', iconClassName)} />
        {title}
        <span className="text-xs font-normal text-muted-foreground">
          ({items.length})
        </span>
      </h3>
      {variant === 'tags' ? (
        <div className="flex flex-wrap gap-2">
          {items.map((item, i) => (
            <Badge key={i} variant="secondary">
              {item}
            </Badge>
          ))}
        </div>
      ) : (
        <ul className="space-y-1.5">
          {items.map((item, i) => (
            <li
              key={i}
              className="flex gap-2 text-sm text-muted-foreground"
            >
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/40" />
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
