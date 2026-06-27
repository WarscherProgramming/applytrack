import { useState } from 'react';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { formatDateTime } from '@/utils/format';

import { useCoverLetterVersions } from '../hooks';

interface VersionCompareProps {
  /** The saved cover-letter name whose versions to compare against. */
  name: string;
  /** The current (edited) draft to compare with a saved version. */
  currentText: string;
}

/** Side-by-side comparison of the current draft and a saved library version. */
export function VersionCompare({ name, currentText }: VersionCompareProps) {
  const { data: versions, isLoading } = useCoverLetterVersions(name);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading versions…</p>;
  }
  if (!versions || versions.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No saved versions yet. Save this letter to build a version history.
      </p>
    );
  }

  const selected = versions.find((v) => v.id === selectedId) ?? null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Compare with:</span>
        <Select
          value={selectedId ?? ''}
          onValueChange={(v) => setSelectedId(v)}
        >
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select a saved version" />
          </SelectTrigger>
          <SelectContent>
            {versions.map((v) => (
              <SelectItem key={v.id} value={v.id}>
                v{v.version} · {formatDateTime(v.created_at)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {selected ? (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">
              Saved v{selected.version}
            </p>
            <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-lg border bg-muted/30 p-3 text-xs">
              {selected.content}
            </pre>
          </div>
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">
              Current draft
            </p>
            <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-lg border bg-muted/30 p-3 text-xs">
              {currentText}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  );
}
