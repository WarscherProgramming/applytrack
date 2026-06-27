import { Sparkles } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

/**
 * Progress indicator shown while a prep package is generated.
 *
 * Generation is a single synchronous request (real token streaming would
 * require new transport infrastructure, excluded by this milestone), so this
 * communicates progress with an animated treatment rather than streaming tokens.
 */
export function GeneratingIndicator() {
  return (
    <Card>
      <CardContent className="space-y-4 py-6">
        <div className="flex items-center gap-2 text-sm font-medium text-primary">
          <Sparkles className="h-4 w-4 animate-pulse" />
          Preparing your interview package
          <span className="inline-flex gap-0.5">
            <span className="animate-bounce [animation-delay:-0.3s]">.</span>
            <span className="animate-bounce [animation-delay:-0.15s]">.</span>
            <span className="animate-bounce">.</span>
          </span>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
