import { ChevronDown } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useState, type ReactNode } from 'react';

import { cn } from '@/lib/utils';

interface CollapsibleSectionProps {
  icon: LucideIcon;
  title: string;
  count?: number;
  defaultOpen?: boolean;
  children: ReactNode;
}

/** A single accordion section with a header toggle. */
export function CollapsibleSection({
  icon: Icon,
  title,
  count,
  defaultOpen = false,
  children,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-lg border">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center gap-2 px-4 py-3 text-left text-sm font-semibold"
      >
        <Icon className="h-4 w-4 text-primary" />
        {title}
        {count != null ? (
          <span className="text-xs font-normal text-muted-foreground">
            ({count})
          </span>
        ) : null}
        <ChevronDown
          className={cn(
            'ml-auto h-4 w-4 text-muted-foreground transition-transform',
            open && 'rotate-180',
          )}
        />
      </button>
      {open ? <div className="border-t px-4 py-3">{children}</div> : null}
    </div>
  );
}
