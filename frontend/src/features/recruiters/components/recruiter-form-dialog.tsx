import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';

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

import {
  useCreateRecruiter,
  useUpdateRecruiter,
} from '../hooks/use-recruiters';
import type {
  Recruiter,
  RecruiterCreateInput,
} from '../types/recruiter.types';
import {
  recruiterFormSchema,
  type RecruiterFormOutput,
  type RecruiterFormValues,
} from './recruiter-form-schema';

interface RecruiterFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Edit mode when provided; create mode otherwise. */
  recruiter?: Recruiter | null;
}

const NONE = 'none';

const EMPTY: RecruiterFormValues = {
  company_id: NONE,
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  title: '',
  linkedin_url: '',
  notes: '',
};

/** Create/edit recruiter dialog. One component serves both modes. */
export function RecruiterFormDialog({
  open,
  onOpenChange,
  recruiter,
}: RecruiterFormDialogProps) {
  const isEdit = Boolean(recruiter);
  const { toast } = useToast();
  const { options: companies } = useCompanyOptions();
  const createRecruiter = useCreateRecruiter();
  const updateRecruiter = useUpdateRecruiter();

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<RecruiterFormValues>({
    resolver: zodResolver(recruiterFormSchema),
    defaultValues: EMPTY,
  });

  useEffect(() => {
    if (!open) return;
    reset(
      recruiter
        ? {
            company_id: recruiter.company_id ?? NONE,
            first_name: recruiter.first_name ?? '',
            last_name: recruiter.last_name ?? '',
            email: recruiter.email ?? '',
            phone: recruiter.phone ?? '',
            title: recruiter.title ?? '',
            linkedin_url: recruiter.linkedin_url ?? '',
            notes: recruiter.notes ?? '',
          }
        : EMPTY,
    );
  }, [open, recruiter, reset]);

  const isPending = createRecruiter.isPending || updateRecruiter.isPending;

  const onSubmit = handleSubmit((values) => {
    const output = values as unknown as RecruiterFormOutput;
    // Build the full desired state; nulls clear fields on PATCH.
    const payload: RecruiterCreateInput = {
      company_id: output.company_id === NONE ? null : output.company_id,
      first_name: output.first_name ?? null,
      last_name: output.last_name ?? null,
      email: output.email ?? null,
      phone: output.phone ?? null,
      title: output.title ?? null,
      linkedin_url: output.linkedin_url ?? null,
      notes: output.notes ?? null,
    };

    const label =
      [payload.first_name, payload.last_name].filter(Boolean).join(' ') ||
      payload.email ||
      'Recruiter';

    const onError = (error: unknown, action: string) =>
      toast({
        variant: 'destructive',
        title: `Could not ${action} recruiter`,
        description: getErrorMessage(error),
      });

    if (isEdit && recruiter) {
      updateRecruiter.mutate(
        { id: recruiter.id, input: payload },
        {
          onSuccess: () => {
            toast({ title: 'Recruiter updated', description: label });
            onOpenChange(false);
          },
          onError: (e) => onError(e, 'update'),
        },
      );
    } else {
      createRecruiter.mutate(payload, {
        onSuccess: () => {
          toast({ title: 'Recruiter created', description: label });
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
          <DialogTitle>{isEdit ? 'Edit recruiter' : 'Add recruiter'}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? 'Update this contact’s details.'
              : 'Add a recruiter or contact. Provide at least a name or email.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="first_name">First name</Label>
              <Input
                id="first_name"
                autoFocus
                {...register('first_name')}
                aria-invalid={!!errors.first_name}
              />
              {errors.first_name ? (
                <p className="text-xs text-destructive">
                  {errors.first_name.message}
                </p>
              ) : null}
            </div>
            <div className="space-y-2">
              <Label htmlFor="last_name">Last name</Label>
              <Input id="last_name" {...register('last_name')} />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@company.com"
                {...register('email')}
                aria-invalid={!!errors.email}
              />
              {errors.email ? (
                <p className="text-xs text-destructive">{errors.email.message}</p>
              ) : null}
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" {...register('phone')} />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input id="title" placeholder="e.g. Technical Recruiter" {...register('title')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="company_id">Company</Label>
              <Controller
                control={control}
                name="company_id"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="company_id">
                      <SelectValue placeholder="No company" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={NONE}>No company</SelectItem>
                      {companies.map((company) => (
                        <SelectItem key={company.id} value={company.id}>
                          {company.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="linkedin_url">LinkedIn URL</Label>
            <Input
              id="linkedin_url"
              placeholder="https://linkedin.com/in/…"
              {...register('linkedin_url')}
            />
            {errors.linkedin_url ? (
              <p className="text-xs text-destructive">
                {errors.linkedin_url.message}
              </p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea id="notes" rows={3} {...register('notes')} />
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
              {isEdit ? 'Save changes' : 'Create recruiter'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
