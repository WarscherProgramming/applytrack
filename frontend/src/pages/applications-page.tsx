import { Briefcase, Plus } from 'lucide-react';
import { useRef, useState } from 'react';

import { ConfirmDeleteDialog } from '@/components/common/confirm-delete-dialog';
import { EmptyState } from '@/components/common/empty-state';
import { ErrorState } from '@/components/common/error-state';
import { LoadingSpinner } from '@/components/common/loading-spinner';
import { PageHeader } from '@/components/common/page-header';
import { SearchBar } from '@/components/common/search-bar';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ApplicationBoard } from '@/features/applications/components/application-board';
import { ApplicationFormDialog } from '@/features/applications/components/application-form-dialog';
import { APPLICATION_STATUSES } from '@/features/applications/constants';
import {
  useApplications,
  useDeleteApplication,
} from '@/features/applications/hooks/use-applications';
import type {
  Application,
  ApplicationStatus,
} from '@/features/applications/types/application.types';
import { useCompanyOptions } from '@/features/companies/hooks/use-company-options';
import { getErrorMessage } from '@/lib/errors';
import { useHotkeys } from '@/hooks/use-hotkeys';
import { useToast } from '@/hooks/use-toast';
import { humanizeEnum } from '@/utils/format';

// Kanban needs the whole board at once; 100 is the backend's max page size and
// comfortably covers a single user's pipeline. (Documented foundation limit.)
const BOARD_LIMIT = 100;
const ALL = 'all';

export function ApplicationsPage() {
  const { toast } = useToast();

  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<ApplicationStatus | typeof ALL>(
    ALL,
  );
  const [companyFilter, setCompanyFilter] = useState<string>(ALL);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Application | null>(null);
  const [deleting, setDeleting] = useState<Application | null>(null);

  const searchInputRef = useRef<HTMLInputElement>(null);

  const dialogOpen = formOpen || Boolean(deleting);
  useHotkeys(
    {
      '/': (e) => {
        e.preventDefault();
        searchInputRef.current?.focus();
      },
      c: () => openCreate(),
    },
    !dialogOpen,
  );

  const { options: companies, byId: companyById } = useCompanyOptions();

  const { data, isLoading, isError, error, refetch } = useApplications({
    query: query || undefined,
    status: statusFilter === ALL ? undefined : statusFilter,
    company_id: companyFilter === ALL ? undefined : companyFilter,
    skip: 0,
    limit: BOARD_LIMIT,
  });

  const deleteApplication = useDeleteApplication();

  const applications = data?.items ?? [];
  const total = data?.total ?? 0;
  const hasFilters = query !== '' || statusFilter !== ALL || companyFilter !== ALL;

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(application: Application) {
    setEditing(application);
    setFormOpen(true);
  }

  function confirmDelete() {
    if (!deleting) return;
    deleteApplication.mutate(deleting.id, {
      onSuccess: () => {
        toast({ title: 'Application deleted', description: deleting.job_title });
        setDeleting(null);
      },
      onError: (err) =>
        toast({
          variant: 'destructive',
          title: 'Could not delete application',
          description: getErrorMessage(err),
        }),
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Applications"
        description="Track every application across your pipeline."
        actions={
          <Button onClick={openCreate} title="Add application (press c)">
            <Plus className="h-4 w-4" />
            Add application
          </Button>
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <SearchBar
          value={query}
          onChange={setQuery}
          placeholder="Search job titles…"
          inputRef={searchInputRef}
          shortcutHint="/"
        />

        <Select
          value={statusFilter}
          onValueChange={(v) => setStatusFilter(v as ApplicationStatus | typeof ALL)}
        >
          <SelectTrigger className="w-full sm:w-44" aria-label="Filter by status">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All statuses</SelectItem>
            {APPLICATION_STATUSES.map((status) => (
              <SelectItem key={status} value={status}>
                {humanizeEnum(status)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={companyFilter} onValueChange={setCompanyFilter}>
          <SelectTrigger className="w-full sm:w-52" aria-label="Filter by company">
            <SelectValue placeholder="All companies" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All companies</SelectItem>
            {companies.map((company) => (
              <SelectItem key={company.id} value={company.id}>
                {company.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : isLoading ? (
        <LoadingSpinner label="Loading applications…" />
      ) : total === 0 ? (
        <EmptyState
          icon={Briefcase}
          title={hasFilters ? 'No applications match your filters' : 'No applications yet'}
          description={
            hasFilters
              ? 'Try adjusting your search or filters.'
              : 'Add your first application to start building your pipeline.'
          }
          action={
            !hasFilters ? (
              <Button onClick={openCreate}>
                <Plus className="h-4 w-4" />
                Add application
              </Button>
            ) : undefined
          }
        />
      ) : (
        <ApplicationBoard
          applications={applications}
          companyById={companyById}
          onEdit={openEdit}
          onDelete={setDeleting}
        />
      )}

      <ApplicationFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        application={editing}
      />

      <ConfirmDeleteDialog
        open={Boolean(deleting)}
        onOpenChange={(open) => !open && setDeleting(null)}
        onConfirm={confirmDelete}
        resourceName={deleting?.job_title}
        isPending={deleteApplication.isPending}
      />
    </div>
  );
}
