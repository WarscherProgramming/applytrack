import { zodResolver } from '@hookform/resolvers/zod';
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
import { useCompanyOptions } from '@/features/companies/hooks/use-company-options';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';
import { humanizeEnum } from '@/utils/format';

import { APPLICATION_STATUSES } from '../constants';
import {
  useCreateApplication,
  useUpdateApplication,
} from '../hooks/use-applications';
import type { Application } from '../types/application.types';
import {
  applicationFormSchema,
  type ApplicationFormOutput,
  type ApplicationFormValues,
} from './application-form-schema';

interface ApplicationFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Edit mode when provided; create mode otherwise. */
  application?: Application | null;
  /** Pre-selects a status in create mode (e.g. when adding to a column). */
  defaultStatus?: (typeof APPLICATION_STATUSES)[number];
}

const EMPTY: ApplicationFormValues = {
  company_id: '',
  job_title: '',
  job_link: '',
  location: '',
  salary_range: '',
  status: 'draft',
  date_applied: '',
  source: '',
  notes: '',
};

/** Create/edit application dialog. One component serves both modes. */
export function ApplicationFormDialog({
  open,
  onOpenChange,
  application,
  defaultStatus,
}: ApplicationFormDialogProps) {
  const isEdit = Boolean(application);
  const { toast } = useToast();
  const { options, isLoading: companiesLoading } = useCompanyOptions();
  const createApplication = useCreateApplication();
  const updateApplication = useUpdateApplication();

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ApplicationFormValues>({
    resolver: zodResolver(applicationFormSchema),
    defaultValues: EMPTY,
  });

  // Reset to the active application (edit) or blanks (create) when opened.
  useEffect(() => {
    if (!open) return;
    reset(
      application
        ? {
            company_id: application.company_id,
            job_title: application.job_title,
            job_link: application.job_link ?? '',
            location: application.location ?? '',
            salary_range: application.salary_range ?? '',
            status: application.status,
            date_applied: application.date_applied ?? '',
            source: application.source ?? '',
            notes: application.notes ?? '',
          }
        : { ...EMPTY, status: defaultStatus ?? 'draft' },
    );
  }, [open, application, defaultStatus, reset]);

  const isPending = createApplication.isPending || updateApplication.isPending;
  const noCompanies = !companiesLoading && options.length === 0;

  const onSubmit = handleSubmit((values) => {
    const payload = values as unknown as ApplicationFormOutput;

    const onError = (error: unknown, action: string) =>
      toast({
        variant: 'destructive',
        title: `Could not ${action} application`,
        description: getErrorMessage(error),
      });

    if (isEdit && application) {
      updateApplication.mutate(
        { id: application.id, input: payload },
        {
          onSuccess: () => {
            toast({ title: 'Application updated', description: payload.job_title });
            onOpenChange(false);
          },
          onError: (e) => onError(e, 'update'),
        },
      );
    } else {
      createApplication.mutate(payload, {
        onSuccess: () => {
          toast({ title: 'Application created', description: payload.job_title });
          onOpenChange(false);
        },
        onError: (e) => onError(e, 'create'),
      });
    }
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit application' : 'Add application'}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? 'Update the details of this application.'
              : 'Track a new job application through your pipeline.'}
          </DialogDescription>
        </DialogHeader>

        {noCompanies ? (
          <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
            You need a company first.{' '}
            <Link to="/companies" className="text-primary hover:underline">
              Add a company
            </Link>{' '}
            before creating an application.
          </div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4" noValidate>
            <div className="space-y-2">
              <Label htmlFor="company_id">
                Company <span className="text-destructive">*</span>
              </Label>
              <Controller
                control={control}
                name="company_id"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="company_id" aria-invalid={!!errors.company_id}>
                      <SelectValue placeholder="Select a company" />
                    </SelectTrigger>
                    <SelectContent>
                      {options.map((company) => (
                        <SelectItem key={company.id} value={company.id}>
                          {company.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.company_id ? (
                <p className="text-xs text-destructive">{errors.company_id.message}</p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="job_title">
                Job title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="job_title"
                autoFocus
                {...register('job_title')}
                aria-invalid={!!errors.job_title}
              />
              {errors.job_title ? (
                <p className="text-xs text-destructive">{errors.job_title.message}</p>
              ) : null}
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="job_link">Job link</Label>
                <Input id="job_link" placeholder="https://…" {...register('job_link')} />
                {errors.job_link ? (
                  <p className="text-xs text-destructive">{errors.job_link.message}</p>
                ) : null}
              </div>
              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input id="location" {...register('location')} />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="salary_range">Salary range</Label>
                <Input id="salary_range" placeholder="e.g. $120k–$150k" {...register('salary_range')} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="date_applied">Date applied</Label>
                <Input id="date_applied" type="date" {...register('date_applied')} />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="status">
                  Status <span className="text-destructive">*</span>
                </Label>
                <Controller
                  control={control}
                  name="status"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger id="status">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {APPLICATION_STATUSES.map((status) => (
                          <SelectItem key={status} value={status}>
                            {humanizeEnum(status)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="source">Source</Label>
                <Input id="source" placeholder="e.g. LinkedIn" {...register('source')} />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea id="notes" rows={3} {...register('notes')} />
              {errors.notes ? (
                <p className="text-xs text-destructive">{errors.notes.message}</p>
              ) : null}
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
                {isEdit ? 'Save changes' : 'Create application'}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
