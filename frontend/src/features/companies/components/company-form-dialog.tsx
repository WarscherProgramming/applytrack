import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';

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
import { Textarea } from '@/components/ui/textarea';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';

import { useCreateCompany, useUpdateCompany } from '../hooks/use-companies';
import type { Company } from '../types/company.types';
import {
  companyFormSchema,
  type CompanyFormOutput,
  type CompanyFormValues,
} from './company-form-schema';

interface CompanyFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** When provided, the dialog is in edit mode; otherwise create mode. */
  company?: Company | null;
}

const EMPTY: CompanyFormValues = {
  name: '',
  website: '',
  industry: '',
  location: '',
  notes: '',
};

/** Create/edit company dialog. One component serves both modes. */
export function CompanyFormDialog({
  open,
  onOpenChange,
  company,
}: CompanyFormDialogProps) {
  const isEdit = Boolean(company);
  const { toast } = useToast();
  const createCompany = useCreateCompany();
  const updateCompany = useUpdateCompany();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CompanyFormValues>({
    resolver: zodResolver(companyFormSchema),
    defaultValues: EMPTY,
  });

  // Reset the form to the active company (or blank) whenever the dialog opens.
  useEffect(() => {
    if (!open) return;
    reset(
      company
        ? {
            name: company.name,
            website: company.website ?? '',
            industry: company.industry ?? '',
            location: company.location ?? '',
            notes: company.notes ?? '',
          }
        : EMPTY,
    );
  }, [open, company, reset]);

  const isPending = createCompany.isPending || updateCompany.isPending;

  const onSubmit = handleSubmit((values) => {
    // zod transforms blanks → undefined; cast to the parsed output shape.
    const payload = values as unknown as CompanyFormOutput;

    if (isEdit && company) {
      updateCompany.mutate(
        { id: company.id, input: payload },
        {
          onSuccess: () => {
            toast({ title: 'Company updated', description: payload.name });
            onOpenChange(false);
          },
          onError: (error) =>
            toast({
              variant: 'destructive',
              title: 'Could not update company',
              description: getErrorMessage(error),
            }),
        },
      );
    } else {
      createCompany.mutate(payload, {
        onSuccess: () => {
          toast({ title: 'Company created', description: payload.name });
          onOpenChange(false);
        },
        onError: (error) =>
          toast({
            variant: 'destructive',
            title: 'Could not create company',
            description: getErrorMessage(error),
          }),
      });
    }
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit company' : 'Add company'}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? 'Update the company details below.'
              : 'Add a company to track applications and contacts.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="name">
              Name <span className="text-destructive">*</span>
            </Label>
            <Input id="name" autoFocus {...register('name')} aria-invalid={!!errors.name} />
            {errors.name ? (
              <p className="text-xs text-destructive">{errors.name.message}</p>
            ) : null}
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="website">Website</Label>
              <Input id="website" placeholder="https://…" {...register('website')} />
              {errors.website ? (
                <p className="text-xs text-destructive">{errors.website.message}</p>
              ) : null}
            </div>
            <div className="space-y-2">
              <Label htmlFor="industry">Industry</Label>
              <Input id="industry" {...register('industry')} />
              {errors.industry ? (
                <p className="text-xs text-destructive">{errors.industry.message}</p>
              ) : null}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="location">Location</Label>
            <Input id="location" {...register('location')} />
            {errors.location ? (
              <p className="text-xs text-destructive">{errors.location.message}</p>
            ) : null}
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
              {isEdit ? 'Save changes' : 'Create company'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
