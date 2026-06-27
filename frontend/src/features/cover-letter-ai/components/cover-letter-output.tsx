import { Copy, Download, GitCompare, RefreshCw, Save } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';

import { useSaveCoverLetter } from '../hooks';
import { downloadTextFile, slugify } from '../lib';
import type { GenerationHistoryEntry } from '../types';
import { UsageSummary } from './usage-summary';
import { VersionCompare } from './version-compare';

interface CoverLetterOutputProps {
  generation: GenerationHistoryEntry;
  isRegenerating: boolean;
  onRegenerate: () => void;
}

type Tab = 'markdown' | 'plain';

/**
 * Read/edit view of a generated letter with copy, download, save-as-version,
 * regenerate, and version comparison. Remounts per generation (keyed by id in
 * the page) so its local edit state resets cleanly each time.
 */
export function CoverLetterOutput({
  generation,
  isRegenerating,
  onRegenerate,
}: CoverLetterOutputProps) {
  const { toast } = useToast();
  const save = useSaveCoverLetter();

  const [tab, setTab] = useState<Tab>('markdown');
  const [markdown, setMarkdown] = useState(generation.markdown);
  const [saveName, setSaveName] = useState(
    `${generation.company_name} - ${generation.job_title}`,
  );
  const [showCompare, setShowCompare] = useState(false);

  const activeText = tab === 'markdown' ? markdown : generation.plain_text;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(activeText);
      toast({ title: 'Copied to clipboard' });
    } catch {
      toast({ variant: 'destructive', title: 'Could not copy' });
    }
  }

  function handleDownload() {
    const ext = tab === 'markdown' ? 'md' : 'txt';
    downloadTextFile(
      `${slugify(saveName)}.${ext}`,
      activeText,
      tab === 'markdown' ? 'text/markdown' : 'text/plain',
    );
  }

  function handleSave() {
    if (!saveName.trim()) {
      toast({ variant: 'destructive', title: 'Enter a name to save' });
      return;
    }
    save.mutate(
      { name: saveName.trim(), content: markdown },
      {
        onSuccess: (saved) =>
          toast({
            title: 'Saved to Cover Letter Library',
            description: `${saved.name} · v${saved.version}`,
          }),
        onError: (error) =>
          toast({
            variant: 'destructive',
            title: 'Could not save',
            description: getErrorMessage(error),
          }),
      },
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <CardTitle>Generated cover letter</CardTitle>
          <p className="text-sm text-muted-foreground">
            {generation.company_name} · {generation.job_title} ·{' '}
            {generation.resume_name}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            <Copy className="h-4 w-4" />
            Copy
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownload}>
            <Download className="h-4 w-4" />
            Download
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onRegenerate}
            disabled={isRegenerating}
          >
            <RefreshCw
              className={cn('h-4 w-4', isRegenerating && 'animate-spin')}
            />
            Regenerate
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <UsageSummary usage={generation.usage} />

        {/* Format toggle */}
        <div className="inline-flex rounded-lg border p-0.5 text-sm">
          {(['markdown', 'plain'] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={cn(
                'rounded-md px-3 py-1 font-medium transition-colors',
                tab === t
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {t === 'markdown' ? 'Markdown' : 'Plain text'}
            </button>
          ))}
        </div>

        {tab === 'markdown' ? (
          <Textarea
            value={markdown}
            onChange={(e) => setMarkdown(e.target.value)}
            rows={16}
            className="font-mono text-sm"
            aria-label="Editable cover letter (Markdown)"
          />
        ) : (
          <pre className="max-h-[28rem] overflow-auto whitespace-pre-wrap rounded-lg border bg-muted/30 p-4 text-sm">
            {generation.plain_text}
          </pre>
        )}

        {/* Save as new version */}
        <div className="space-y-2 rounded-lg border p-4">
          <Label htmlFor="cl-savename">Save as new version</Label>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              id="cl-savename"
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              placeholder="Cover letter name"
            />
            <Button onClick={handleSave} disabled={save.isPending}>
              <Save className="h-4 w-4" />
              Save version
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Saving under an existing name adds a new version to that letter.
          </p>
        </div>

        {/* Compare with previous versions */}
        <div className="space-y-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowCompare((v) => !v)}
            className="text-muted-foreground"
          >
            <GitCompare className="h-4 w-4" />
            {showCompare ? 'Hide comparison' : 'Compare with previous versions'}
          </Button>
          {showCompare ? (
            <VersionCompare name={saveName.trim()} currentText={markdown} />
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
