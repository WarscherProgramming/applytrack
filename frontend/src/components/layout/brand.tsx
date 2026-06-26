import { Briefcase } from 'lucide-react';

import { cn } from '@/lib/utils';

/** App wordmark with logo, used in the sidebar and mobile header. */
export function Brand({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
        <Briefcase className="h-5 w-5" />
      </div>
      <div className="flex flex-col leading-none">
        <span className="text-base font-semibold tracking-tight">ApplyTrack</span>
        <span className="text-xs text-muted-foreground">Job Search CRM</span>
      </div>
    </div>
  );
}
