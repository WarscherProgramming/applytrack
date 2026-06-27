import { useState } from 'react';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { formatDate } from '@/utils/format';

import { usePrep } from '../hooks';
import { packageToMarkdown } from '../lib';
import type { InterviewPrepListItem, InterviewPrepPackage } from '../types';

interface VersionCompareProps {
  current: InterviewPrepPackage;
  /** Other packages available to compare against (history minus current). */
  others: InterviewPrepListItem[];
}

/** Side-by-side comparison of the current package and a previous one. */
export function VersionCompare({ current, others }: VersionCompareProps) {
  const [compareId, setCompareId] = useState<string | null>(null);
  const comparison = usePrep(compareId);

  if (others.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Generate more packages to compare versions.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Compare with:</span>
        <Select value={compareId ?? ''} onValueChange={setCompareId}>
          <SelectTrigger className="w-72">
            <SelectValue placeholder="Select a previous package" />
          </SelectTrigger>
          <SelectContent>
            {others.map((o) => (
              <SelectItem key={o.id} value={o.id}>
                {o.company_name} · {o.job_title} ({formatDate(o.created_at)})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {comparison.data ? (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">
              Previous · {formatDate(comparison.data.created_at)}
            </p>
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-lg border bg-muted/30 p-3 text-xs">
              {packageToMarkdown(comparison.data)}
            </pre>
          </div>
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">
              Current · {formatDate(current.created_at)}
            </p>
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-lg border bg-muted/30 p-3 text-xs">
              {packageToMarkdown(current)}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  );
}
