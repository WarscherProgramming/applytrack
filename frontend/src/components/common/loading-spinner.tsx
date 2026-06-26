import { Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  className?: string;
  /** Optional message rendered below the spinner. */
  label?: string;
  size?: number;
}

/** A centered spinner for loading states. */
export function LoadingSpinner({
  className,
  label,
  size = 24,
}: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        'flex flex-col items-center justify-center gap-3 py-10 text-muted-foreground',
        className,
      )}
    >
      <Loader2 className="animate-spin" style={{ width: size, height: size }} />
      {label ? <span className="text-sm">{label}</span> : null}
      <span className="sr-only">Loading</span>
    </div>
  );
}
