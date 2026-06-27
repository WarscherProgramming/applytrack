import { GitCompare, Sparkles } from 'lucide-react';
import { useState } from 'react';

import { ConfirmDeleteDialog } from '@/components/common/confirm-delete-dialog';
import { ErrorState } from '@/components/common/error-state';
import { PageHeader } from '@/components/common/page-header';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { GenerationForm } from '@/features/interview-prep/components/generation-form';
import { GeneratingIndicator } from '@/features/interview-prep/components/generating-indicator';
import { HistoryPanel } from '@/features/interview-prep/components/history-panel';
import { PrepResult } from '@/features/interview-prep/components/prep-result';
import { VersionCompare } from '@/features/interview-prep/components/version-compare';
import {
  useDeletePrep,
  useGeneratePrep,
  usePrep,
  usePrepHistory,
} from '@/features/interview-prep/hooks';
import type {
  InterviewPrepListItem,
  InterviewPrepRequest,
} from '@/features/interview-prep/types';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';

export function InterviewPrepPage() {
  const { toast } = useToast();
  const generate = useGeneratePrep();
  const deletePrep = useDeletePrep();
  const history = usePrepHistory();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [lastInput, setLastInput] = useState<InterviewPrepRequest | null>(null);
  const [deleting, setDeleting] = useState<InterviewPrepListItem | null>(null);
  const [showCompare, setShowCompare] = useState(false);

  const current = usePrep(selectedId);

  function run(input: InterviewPrepRequest) {
    setLastInput(input);
    generate.mutate(input, {
      onSuccess: (pkg) => {
        setSelectedId(pkg.id);
        setShowCompare(false);
        toast({ title: 'Preparation ready', description: `${pkg.company_name} · ${pkg.job_title}` });
      },
      onError: (error) =>
        toast({
          variant: 'destructive',
          title: 'Could not generate preparation',
          description: getErrorMessage(error),
        }),
    });
  }

  function confirmDelete() {
    if (!deleting) return;
    deletePrep.mutate(deleting.id, {
      onSuccess: () => {
        if (selectedId === deleting.id) setSelectedId(null);
        toast({ title: 'Package deleted' });
        setDeleting(null);
      },
      onError: (error) =>
        toast({
          variant: 'destructive',
          title: 'Could not delete package',
          description: getErrorMessage(error),
        }),
    });
  }

  const items = history.data?.items ?? [];
  const others = items.filter((i) => i.id !== selectedId);

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Interview Prep"
        description="Generate a complete preparation package for a specific interview."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Prepare</CardTitle>
              <CardDescription>
                Select an application (or enter details) and generate. Every
                package is saved to your history.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <GenerationForm isGenerating={generate.isPending} onGenerate={run} />
            </CardContent>
          </Card>

          {generate.isPending ? (
            <GeneratingIndicator />
          ) : current.isError ? (
            <ErrorState error={current.error} onRetry={current.refetch} />
          ) : current.data ? (
            <>
              <PrepResult
                package={current.data}
                isRegenerating={generate.isPending}
                onRegenerate={() => lastInput && run(lastInput)}
              />
              <Card>
                <CardContent className="space-y-3 py-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowCompare((v) => !v)}
                    className="text-muted-foreground"
                  >
                    <GitCompare className="h-4 w-4" />
                    {showCompare ? 'Hide comparison' : 'Compare previous versions'}
                  </Button>
                  {showCompare ? (
                    <VersionCompare current={current.data} others={others} />
                  ) : null}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-base font-semibold">No package yet</h3>
                  <p className="mx-auto max-w-sm text-sm text-muted-foreground">
                    Generate a preparation package or reopen one from your history.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>History</CardTitle>
              <CardDescription>Click to reopen a saved package.</CardDescription>
            </CardHeader>
            <CardContent>
              {history.isError ? (
                <ErrorState error={history.error} onRetry={history.refetch} />
              ) : (
                <HistoryPanel
                  items={items}
                  selectedId={selectedId}
                  isLoading={history.isLoading}
                  onSelect={setSelectedId}
                  onDelete={setDeleting}
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <ConfirmDeleteDialog
        open={Boolean(deleting)}
        onOpenChange={(open) => !open && setDeleting(null)}
        onConfirm={confirmDelete}
        title="Delete package"
        resourceName={
          deleting ? `${deleting.company_name} · ${deleting.job_title}` : undefined
        }
        isPending={deletePrep.isPending}
      />
    </div>
  );
}
