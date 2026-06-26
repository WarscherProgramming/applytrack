import { zodResolver } from '@hookform/resolvers/zod';
import { format, parseISO } from 'date-fns';
import { Loader2 } from 'lucide-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useApplicationOptions } from '@/features/applications/hooks/use-application-options';
import { useRecruiterOptions } from '@/features/recruiters/hooks/use-recruiter-options';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';
import { humanizeEnum } from '@/utils/format';

import { INTERVIEW_STATUSES, INTERVIEW_TYPES } from '../constants';
import {
  useCreateInterview,
  useUpdateInterview,
} from '../hooks/use-interviews';
import type {
  Interview,
  InterviewCreateInput,
  InterviewType,
} from '../types/interview.types';
import {
  interviewFormSchema,
  type InterviewFormOutput,
  type InterviewFormValues,
} from './interview-form-schema';

interface InterviewFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Edit mode when provided; create mode otherwise. */
  interview?: Interview | null;
  /** Pre-fills the date in create mode (e.g. clicking a calendar day). */
  defaultStart?: Date | null;
}

const NONE = 'none';
const LOCAL_FORMAT = "yyyy-MM-dd'T'HH:mm";

/** Default new interviews to the next full hour. */
function nextHour(base = new Date()): Date {
  const d = new Date(base);
  d.setMinutes(0, 0, 0);
  d.setHours(d.getHours() + 1);
  return d;
}

export function InterviewFormDialog({
  open,
  onOpenChange,
  interview,
  defaultStart,
}: InterviewFormDialogProps) {
  const isEdit = Boolean(interview);
  const { toast } = useToast();
  const { options: applications, byId: applicationById, isLoading: appsLoading } =
    useApplicationOptions();
  const { options: recruiters } = useRecruiterOptions();
  const createInterview = useCreateInterview();
  const updateInterview = useUpdateInterview();

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<InterviewFormValues>({
    resolver: zodResolver(interviewFormSchema),
  });

  useEffect(() => {
    if (!open) return;
    reset(
      interview
        ? {
            application_id: interview.application_id,
            recruiter_id: interview.recruiter_id ?? NONE,
            interview_type: interview.interview_type ?? NONE,
            scheduled_at: format(parseISO(interview.scheduled_at), LOCAL_FORMAT),
            duration_minutes: interview.duration_minutes,
            location: interview.location ?? '',
            meeting_link: interview.meeting_link ?? '',
            status: interview.status,
            notes: interview.notes ?? '',
            feedback: interview.feedback ?? '',
          }
        : {
            application_id: '',
            recruiter_id: NONE,
            interview_type: NONE,
            scheduled_at: format(nextHour(defaultStart ?? undefined), LOCAL_FORMAT),
            duration_minutes: 30,
            location: '',
            meeting_link: '',
            status: 'scheduled',
            notes: '',
            feedback: '',
          },
    );
  }, [open, interview, defaultStart, reset]);

  const isPending = createInterview.isPending || updateInterview.isPending;
  const noApplications = !appsLoading && applications.length === 0;

  const onSubmit = handleSubmit((values) => {
    const output = values as unknown as InterviewFormOutput;
    const payload: InterviewCreateInput = {
      application_id: output.application_id,
      recruiter_id: output.recruiter_id === NONE ? null : output.recruiter_id,
      interview_type:
        output.interview_type === NONE
          ? null
          : (output.interview_type as InterviewType),
      scheduled_at: new Date(output.scheduled_at).toISOString(),
      duration_minutes: output.duration_minutes,
      location: output.location ?? null,
      meeting_link: output.meeting_link ?? null,
      status: output.status,
      notes: output.notes ?? null,
      feedback: output.feedback ?? null,
    };

    const label = applicationById.get(output.application_id)?.job_title ?? 'Interview';
    const onError = (error: unknown, action: string) =>
      toast({
        variant: 'destructive',
        title: `Could not ${action} interview`,
        description: getErrorMessage(error),
      });

    if (isEdit && interview) {
      updateInterview.mutate(
        { id: interview.id, input: payload },
        {
          onSuccess: () => {
            toast({ title: 'Interview updated', description: label });
            onOpenChange(false);
          },
          onError: (e) => onError(e, 'update'),
        },
      );
    } else {
      createInterview.mutate(payload, {
        onSuccess: () => {
          toast({ title: 'Interview scheduled', description: label });
          onOpenChange(false);
        },
        onError: (e) => onError(e, 'schedule'),
      });
    }
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit interview' : 'Schedule interview'}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? 'Update the details of this interview.'
              : 'Schedule an interview for one of your applications.'}
          </DialogDescription>
        </DialogHeader>

        {noApplications ? (
          <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
            You need an application first.{' '}
            <Link to="/applications" className="text-primary hover:underline">
              Add an application
            </Link>{' '}
            before scheduling an interview.
          </div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4" noValidate>
            <div className="space-y-2">
              <Label htmlFor="application_id">
                Application <span className="text-destructive">*</span>
              </Label>
              <Controller
                control={control}
                name="application_id"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="application_id" aria-invalid={!!errors.application_id}>
                      <SelectValue placeholder="Select an application" />
                    </SelectTrigger>
                    <SelectContent>
                      {applications.map((app) => (
                        <SelectItem key={app.id} value={app.id}>
                          {app.job_title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.application_id ? (
                <p className="text-xs text-destructive">
                  {errors.application_id.message}
                </p>
              ) : null}
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="scheduled_at">
                  Date &amp; time <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="scheduled_at"
                  type="datetime-local"
                  {...register('scheduled_at')}
                  aria-invalid={!!errors.scheduled_at}
                />
                {errors.scheduled_at ? (
                  <p className="text-xs text-destructive">
                    {errors.scheduled_at.message}
                  </p>
                ) : null}
              </div>
              <div className="space-y-2">
                <Label htmlFor="duration_minutes">Duration (minutes)</Label>
                <Input
                  id="duration_minutes"
                  type="number"
                  min={15}
                  max={480}
                  step={5}
                  {...register('duration_minutes')}
                  aria-invalid={!!errors.duration_minutes}
                />
                {errors.duration_minutes ? (
                  <p className="text-xs text-destructive">
                    {errors.duration_minutes.message}
                  </p>
                ) : null}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="interview_type">Type</Label>
                <Controller
                  control={control}
                  name="interview_type"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger id="interview_type">
                        <SelectValue placeholder="No type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={NONE}>No type</SelectItem>
                        {INTERVIEW_TYPES.map((type) => (
                          <SelectItem key={type} value={type}>
                            {humanizeEnum(type)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Controller
                  control={control}
                  name="status"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger id="status">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {INTERVIEW_STATUSES.map((status) => (
                          <SelectItem key={status} value={status}>
                            {humanizeEnum(status)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="recruiter_id">Recruiter</Label>
              <Controller
                control={control}
                name="recruiter_id"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="recruiter_id">
                      <SelectValue placeholder="No recruiter" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={NONE}>No recruiter</SelectItem>
                      {recruiters.map((recruiter) => (
                        <SelectItem key={recruiter.id} value={recruiter.id}>
                          {[recruiter.first_name, recruiter.last_name]
                            .filter(Boolean)
                            .join(' ') ||
                            recruiter.email ||
                            'Recruiter'}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input id="location" placeholder="e.g. Remote / Office" {...register('location')} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="meeting_link">Meeting link</Label>
                <Input id="meeting_link" placeholder="https://…" {...register('meeting_link')} />
                {errors.meeting_link ? (
                  <p className="text-xs text-destructive">
                    {errors.meeting_link.message}
                  </p>
                ) : null}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea id="notes" rows={2} {...register('notes')} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="feedback">Feedback</Label>
              <Textarea id="feedback" rows={2} {...register('feedback')} />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {isEdit ? 'Save changes' : 'Schedule interview'}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
