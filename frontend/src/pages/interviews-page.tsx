import { addMonths, addWeeks, endOfWeek, format, startOfWeek } from 'date-fns';
import { CalendarClock, Plus } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ConfirmDeleteDialog } from '@/components/common/confirm-delete-dialog';
import { EmptyState } from '@/components/common/empty-state';
import { ErrorState } from '@/components/common/error-state';
import { LoadingSpinner } from '@/components/common/loading-spinner';
import { PageHeader } from '@/components/common/page-header';
import { Button } from '@/components/ui/button';
import { AgendaView } from '@/features/calendar/components/agenda-view';
import { CalendarToolbar } from '@/features/calendar/components/calendar-toolbar';
import { MonthView } from '@/features/calendar/components/month-view';
import { WeekView } from '@/features/calendar/components/week-view';
import { interviewsToEvents } from '@/features/calendar/lib/interview-adapter';
import { INTERVIEW_STATUS_STYLE } from '@/features/calendar/lib/status-style';
import type { CalendarEvent, CalendarView } from '@/features/calendar/types';
import { useApplicationOptions } from '@/features/applications/hooks/use-application-options';
import { useCompanyOptions } from '@/features/companies/hooks/use-company-options';
import { InterviewDetailDialog } from '@/features/interviews/components/interview-detail-dialog';
import { InterviewFormDialog } from '@/features/interviews/components/interview-form-dialog';
import { INTERVIEW_STATUSES } from '@/features/interviews/constants';
import {
  useDeleteInterview,
  useInterviews,
} from '@/features/interviews/hooks/use-interviews';
import type { Interview } from '@/features/interviews/types/interview.types';
import { useRecruiterOptions } from '@/features/recruiters/hooks/use-recruiter-options';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';
import { humanizeEnum } from '@/utils/format';

// Calendar needs every interview at once to place them across views; 100 is the
// backend's max page size and covers a single user's schedule. (Foundation cap.)
const CALENDAR_LIMIT = 100;

export function InterviewsPage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [view, setView] = useState<CalendarView>('month');
  const [currentDate, setCurrentDate] = useState(() => new Date());

  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Interview | null>(null);
  const [deleting, setDeleting] = useState<Interview | null>(null);

  const { data, isLoading, isError, error, refetch } = useInterviews({
    skip: 0,
    limit: CALENDAR_LIMIT,
  });
  const { byId: companyById } = useCompanyOptions();
  const { byId: applicationById } = useApplicationOptions();
  const { byId: recruiterById } = useRecruiterOptions();

  const interviews = useMemo(() => data?.items ?? [], [data]);

  const events = useMemo(
    () =>
      interviewsToEvents(interviews, {
        companyById,
        applicationById,
        recruiterById,
      }),
    [interviews, companyById, applicationById, recruiterById],
  );

  const label =
    view === 'month'
      ? format(currentDate, 'MMMM yyyy')
      : view === 'week'
        ? `${format(startOfWeek(currentDate), 'MMM d')} – ${format(
            endOfWeek(currentDate),
            'MMM d, yyyy',
          )}`
        : '';

  function shift(amount: number) {
    if (view === 'month') setCurrentDate((d) => addMonths(d, amount));
    else if (view === 'week') setCurrentDate((d) => addWeeks(d, amount));
  }

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function handleEdit(interview: Interview) {
    setSelectedEvent(null);
    setEditing(interview);
    setFormOpen(true);
  }

  function handleDelete(interview: Interview) {
    setSelectedEvent(null);
    setDeleting(interview);
  }

  function handleViewApplication() {
    setSelectedEvent(null);
    navigate('/applications');
  }

  const deleteInterview = useDeleteInterview();
  function confirmDelete() {
    if (!deleting) return;
    deleteInterview.mutate(deleting.id, {
      onSuccess: () => {
        toast({ title: 'Interview deleted' });
        setDeleting(null);
      },
      onError: (err) =>
        toast({
          variant: 'destructive',
          title: 'Could not delete interview',
          description: getErrorMessage(err),
        }),
    });
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Interviews"
        description="Your interview schedule across month, week, and agenda views."
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Schedule interview
          </Button>
        }
      />

      <CalendarToolbar
        view={view}
        onViewChange={setView}
        label={label}
        onPrev={() => shift(-1)}
        onNext={() => shift(1)}
        onToday={() => setCurrentDate(new Date())}
      />

      {/* Status legend */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        {INTERVIEW_STATUSES.map((status) => (
          <span key={status} className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span
              className={`h-2.5 w-2.5 rounded-full ${INTERVIEW_STATUS_STYLE[status].dot}`}
            />
            {humanizeEnum(status)}
          </span>
        ))}
      </div>

      {isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : isLoading ? (
        <LoadingSpinner label="Loading interviews…" />
      ) : interviews.length === 0 ? (
        <EmptyState
          icon={CalendarClock}
          title="No interviews scheduled"
          description="Schedule your first interview to see it on the calendar."
          action={
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" />
              Schedule interview
            </Button>
          }
        />
      ) : view === 'month' ? (
        <MonthView currentDate={currentDate} events={events} onSelect={setSelectedEvent} />
      ) : view === 'week' ? (
        <WeekView currentDate={currentDate} events={events} onSelect={setSelectedEvent} />
      ) : (
        <AgendaView events={events} onSelect={setSelectedEvent} />
      )}

      <InterviewDetailDialog
        open={Boolean(selectedEvent)}
        onOpenChange={(open) => !open && setSelectedEvent(null)}
        enriched={selectedEvent?.data ?? null}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onViewApplication={handleViewApplication}
      />

      <InterviewFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        interview={editing}
      />

      <ConfirmDeleteDialog
        open={Boolean(deleting)}
        onOpenChange={(open) => !open && setDeleting(null)}
        onConfirm={confirmDelete}
        title="Delete interview"
        description="This permanently removes the interview. This action cannot be undone."
        isPending={deleteInterview.isPending}
      />
    </div>
  );
}
