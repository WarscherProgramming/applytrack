import { Sparkles } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

/**
 * Progress indicator shown while a letter is being generated.
 *
 * The platform's generation is a single synchronous request (real token
 * streaming would require new transport infrastructure, which this milestone
 * explicitly excludes), so this communicates progress with an animated,
 * "drafting" treatment rather than streaming tokens.
 */
export function GeneratingIndicator() {
  return (
    <Card>
      <CardContent className="space-y-4 py-6">
        <div className="flex items-center gap-2 text-sm font-medium text-primary">
          <Sparkles className="h-4 w-4 animate-pulse" />
          Drafting your cover letter
          <span className="inline-flex gap-0.5">
            <span className="animate-bounce [animation-delay:-0.3s]">.</span>
            <span className="animate-bounce [animation-delay:-0.15s]">.</span>
            <span className="animate-bounce">.</span>
          </span>
        </div>
        <div className="space-y-2">
          {['w-3/4', 'w-full', 'w-5/6', 'w-full', 'w-2/3'].map((w, i) => (
            <Skeleton key={i} className={`h-4 ${w} animate-pulse`} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
