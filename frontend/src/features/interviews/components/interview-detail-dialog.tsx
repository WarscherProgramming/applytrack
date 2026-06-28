import { format, parseISO } from 'date-fns';
import {
  Building2,
  CalendarSync,
  CalendarClock,
  Clock,
  Copy,
  ExternalLink,
  LinkIcon,
  MapPin,
  Pencil,
  Trash2,
  UserSquare2,
} from 'lucide-react';
import type { ReactNode } from 'react';

import { StatusBadge } from '@/components/common/status-badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { useSyncInterviewToCalendar } from '@/features/calendar-integration/hooks';
import type { EnrichedInterview } from '@/features/calendar/types';
import { useToast } from '@/hooks/use-toast';
import { humanizeEnum } from '@/utils/format';

interface InterviewDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  enriched: EnrichedInterview | null;
  onEdit: (interview: EnrichedInterview['interview']) => void;
  onDelete: (interview: EnrichedInterview['interview']) => void;
  onViewApplication: (applicationId: string) => void;
}

function DetailRow({ icon, label, children }: { icon: ReactNode; label: string; children: ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <span className="mt-0.5 text-muted-foreground">{icon}</span>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <div className="text-sm">{children}</div>
      </div>
    </div>
  );
}

/** Read-only interview detail with edit/delete/link/application actions. */
export function InterviewDetailDialog({
  open,
  onOpenChange,
  enriched,
  onEdit,
  onDelete,
  onViewApplication,
}: InterviewDetailDialogProps) {
  const { toast } = useToast();
  const syncInterview = useSyncInterviewToCalendar();
  if (!enriched) return null;

  const { interview, companyName, jobTitle, recruiterName } = enriched;
  const start = parseISO(interview.scheduled_at);
  const link = interview.meeting_link;

  async function copyLink() {
    if (!link) return;
    try {
      await navigator.clipboard.writeText(link);
      toast({ title: 'Meeting link copied' });
    } catch {
      toast({ variant: 'destructive', title: 'Could not copy link' });
    }
  }

  function syncToCalendar() {
    syncInterview.mutate(
      { interviewId: interview.id, provider: 'google' },
      {
        onSuccess: (result) =>
          toast({
            title: 'Interview synced',
            description: `${result.created} created, ${result.updated} updated, ${result.skipped} unchanged.`,
          }),
        onError: () =>
          toast({
            variant: 'destructive',
            title: 'Calendar sync failed',
            description: 'Connect Google Calendar from Settings before syncing.',
          }),
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center justify-between gap-3 pr-6">
            <DialogTitle>{jobTitle ?? 'Interview'}</DialogTitle>
            <StatusBadge status={interview.status} />
          </div>
          <DialogDescription>
            {companyName ?? 'Unknown company'}
            {interview.interview_type
              ? ` · ${humanizeEnum(interview.interview_type)}`
              : ''}
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <DetailRow icon={<CalendarClock className="h-4 w-4" />} label="When">
            {format(start, 'EEE, MMM d, yyyy')}
            <br />
            {format(start, 'h:mm a')}
          </DetailRow>
          <DetailRow icon={<Clock className="h-4 w-4" />} label="Duration">
            {interview.duration_minutes} minutes
          </DetailRow>
          <DetailRow icon={<Building2 className="h-4 w-4" />} label="Company">
            {companyName ?? '—'}
          </DetailRow>
          <DetailRow icon={<UserSquare2 className="h-4 w-4" />} label="Recruiter">
            {recruiterName ?? '—'}
          </DetailRow>
          {interview.location ? (
            <DetailRow icon={<MapPin className="h-4 w-4" />} label="Location">
              {interview.location}
            </DetailRow>
          ) : null}
          {link ? (
            <DetailRow icon={<LinkIcon className="h-4 w-4" />} label="Meeting link">
              <a
                href={link}
                target="_blank"
                rel="noreferrer noopener"
                className="break-all text-primary hover:underline"
              >
                {link}
              </a>
            </DetailRow>
          ) : null}
        </div>

        {interview.notes || interview.feedback ? <Separator /> : null}
        {interview.notes ? (
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">Notes</p>
            <p className="whitespace-pre-wrap text-sm">{interview.notes}</p>
          </div>
        ) : null}
        {interview.feedback ? (
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">Feedback</p>
            <p className="whitespace-pre-wrap text-sm">{interview.feedback}</p>
          </div>
        ) : null}

        <Separator />

        <div className="flex flex-wrap gap-2">
          <Button size="sm" onClick={() => onEdit(interview)}>
            <Pencil className="h-4 w-4" />
            Edit
          </Button>
          {link ? (
            <>
              <Button size="sm" variant="outline" onClick={copyLink}>
                <Copy className="h-4 w-4" />
                Copy link
              </Button>
              <Button size="sm" variant="outline" asChild>
                <a href={link} target="_blank" rel="noreferrer noopener">
                  <ExternalLink className="h-4 w-4" />
                  Open link
                </a>
              </Button>
            </>
          ) : null}
          <Button
            size="sm"
            variant="outline"
            onClick={() => onViewApplication(interview.application_id)}
          >
            <Building2 className="h-4 w-4" />
            View application
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={syncToCalendar}
            disabled={syncInterview.isPending}
          >
            <CalendarSync className="h-4 w-4" />
            Sync calendar
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="text-destructive hover:text-destructive"
            onClick={() => onDelete(interview)}
          >
            <Trash2 className="h-4 w-4" />
            Delete
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
