import { Loader2, Sparkles, Wand2 } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

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
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { AnalysisResult } from '@/features/resume-match/components/analysis-result';
import { HistoryList } from '@/features/resume-match/components/history-list';
import {
  useDeleteMatch,
  useMatch,
  useMatchHistory,
  useRunMatch,
} from '@/features/resume-match/hooks';
import type { ResumeMatchListItem } from '@/features/resume-match/types';
import { resumeHooks } from '@/features/resumes/resumes';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';

const MIN_JD = 20;
const MAX_JD = 20_000;

export function ResumeMatchPage() {
  const { toast } = useToast();

  const [resumeId, setResumeId] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<ResumeMatchListItem | null>(null);

  const { options: resumeOptions, isLoading: resumesLoading } =
    resumeHooks.useDocumentOptions();
  const history = useMatchHistory();
  const current = useMatch(selectedId);
  const runMatch = useRunMatch();
  const deleteMatch = useDeleteMatch();

  const jdLength = jobDescription.trim().length;
  const noResumes = !resumesLoading && resumeOptions.length === 0;
  const canRun = Boolean(resumeId) && jdLength >= MIN_JD && !runMatch.isPending;

  function handleRun() {
    if (!canRun) return;
    runMatch.mutate(
      { resume_id: resumeId, job_description: jobDescription.trim() },
      {
        onSuccess: (analysis) => {
          setSelectedId(analysis.id);
          toast({
            title: 'Analysis complete',
            description: `Match score: ${analysis.overall_match_score}/100`,
          });
        },
        onError: (error) =>
          toast({
            variant: 'destructive',
            title: 'Could not analyse resume',
            description: getErrorMessage(error),
          }),
      },
    );
  }

  function confirmDelete() {
    if (!deleting) return;
    deleteMatch.mutate(deleting.id, {
      onSuccess: () => {
        if (selectedId === deleting.id) setSelectedId(null);
        toast({ title: 'Analysis deleted' });
        setDeleting(null);
      },
      onError: (error) =>
        toast({
          variant: 'destructive',
          title: 'Could not delete analysis',
          description: getErrorMessage(error),
        }),
    });
  }

  const items = history.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Resume Match"
        description="Analyse how well a resume matches a job description using AI."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: input + results */}
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>New analysis</CardTitle>
              <CardDescription>
                Pick a resume, paste the job description, and run the match.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {noResumes ? (
                <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                  You need a resume first.{' '}
                  <Link to="/resumes" className="text-primary hover:underline">
                    Upload a resume
                  </Link>{' '}
                  to run a match.
                </div>
              ) : (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="resume">Resume</Label>
                    <Select value={resumeId} onValueChange={setResumeId}>
                      <SelectTrigger id="resume">
                        <SelectValue placeholder="Select a resume" />
                      </SelectTrigger>
                      <SelectContent>
                        {resumeOptions.map((opt) => (
                          <SelectItem key={opt.id} value={opt.id}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="jd">Job description</Label>
                    <Textarea
                      id="jd"
                      rows={10}
                      placeholder="Paste the full job description here…"
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      maxLength={MAX_JD}
                    />
                    <p className="text-xs text-muted-foreground">
                      {jdLength < MIN_JD
                        ? `At least ${MIN_JD} characters (${jdLength}/${MIN_JD}).`
                        : `${jdLength.toLocaleString()} characters`}
                    </p>
                  </div>

                  <Button onClick={handleRun} disabled={!canRun}>
                    {runMatch.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Wand2 className="h-4 w-4" />
                    )}
                    Run analysis
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          {runMatch.isPending ? (
            <Card>
              <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">
                  Analysing resume against the job description…
                </p>
              </CardContent>
            </Card>
          ) : current.isError ? (
            <ErrorState error={current.error} onRetry={current.refetch} />
          ) : current.data ? (
            <AnalysisResult analysis={current.data} />
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-base font-semibold">No analysis selected</h3>
                  <p className="mx-auto max-w-sm text-sm text-muted-foreground">
                    Run a new analysis or reopen a previous one from the history.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right: history */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Previous analyses</CardTitle>
              <CardDescription>Click to reopen.</CardDescription>
            </CardHeader>
            <CardContent>
              {history.isError ? (
                <ErrorState error={history.error} onRetry={history.refetch} />
              ) : (
                <HistoryList
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
        title="Delete analysis"
        resourceName={deleting ? `${deleting.resume_name} match` : undefined}
        isPending={deleteMatch.isPending}
      />
    </div>
  );
}
