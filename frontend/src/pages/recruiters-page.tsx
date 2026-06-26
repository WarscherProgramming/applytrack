import {
  ExternalLink,
  MoreHorizontal,
  Pencil,
  Plus,
  Trash2,
  UserSquare2,
} from 'lucide-react';
import { useRef, useState, type MouseEvent } from 'react';

import { ConfirmDeleteDialog } from '@/components/common/confirm-delete-dialog';
import { DataTable, type DataTableColumn } from '@/components/common/data-table';
import { EmptyState } from '@/components/common/empty-state';
import { ErrorState } from '@/components/common/error-state';
import { PageHeader } from '@/components/common/page-header';
import { Pagination } from '@/components/common/pagination';
import { SearchBar } from '@/components/common/search-bar';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCompanyOptions } from '@/features/companies/hooks/use-company-options';
import { RecruiterFormDialog } from '@/features/recruiters/components/recruiter-form-dialog';
import {
  useDeleteRecruiter,
  useRecruiters,
} from '@/features/recruiters/hooks/use-recruiters';
import type { Recruiter } from '@/features/recruiters/types/recruiter.types';
import { getErrorMessage } from '@/lib/errors';
import { useHotkeys } from '@/hooks/use-hotkeys';
import { useToast } from '@/hooks/use-toast';

const PAGE_SIZE = 10;
const ALL = 'all';

/** Best display label for a recruiter (full name, else email, else fallback). */
function recruiterName(r: Recruiter): string {
  return [r.first_name, r.last_name].filter(Boolean).join(' ') || r.email || '—';
}

const dash = <span className="text-muted-foreground">—</span>;
const stop = (e: MouseEvent) => e.stopPropagation();

export function RecruitersPage() {
  const { toast } = useToast();

  const [query, setQuery] = useState('');
  const [companyFilter, setCompanyFilter] = useState<string>(ALL);
  const [skip, setSkip] = useState(0);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Recruiter | null>(null);
  const [deleting, setDeleting] = useState<Recruiter | null>(null);

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

  const { byId: companyById, options: companies } = useCompanyOptions();

  const { data, isLoading, isError, error, refetch, isFetching } = useRecruiters({
    query: query || undefined,
    company_id: companyFilter === ALL ? undefined : companyFilter,
    skip,
    limit: PAGE_SIZE,
  });

  const deleteRecruiter = useDeleteRecruiter();

  const recruiters = data?.items ?? [];
  const total = data?.total ?? 0;
  const hasFilters = query !== '' || companyFilter !== ALL;

  function handleSearch(value: string) {
    setQuery(value);
    setSkip(0);
  }

  function handleCompanyFilter(value: string) {
    setCompanyFilter(value);
    setSkip(0);
  }

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(recruiter: Recruiter) {
    setEditing(recruiter);
    setFormOpen(true);
  }

  function confirmDelete() {
    if (!deleting) return;
    deleteRecruiter.mutate(deleting.id, {
      onSuccess: () => {
        toast({ title: 'Recruiter deleted', description: recruiterName(deleting) });
        if (recruiters.length === 1 && skip > 0) {
          setSkip((s) => Math.max(0, s - PAGE_SIZE));
        }
        setDeleting(null);
      },
      onError: (err) =>
        toast({
          variant: 'destructive',
          title: 'Could not delete recruiter',
          description: getErrorMessage(err),
        }),
    });
  }

  const columns: DataTableColumn<Recruiter>[] = [
    {
      id: 'name',
      header: 'Name',
      cell: (r) => <span className="font-medium">{recruiterName(r)}</span>,
      sortAccessor: (r) => r.last_name || r.first_name || r.email,
    },
    {
      id: 'title',
      header: 'Title',
      cell: (r) => r.title ?? dash,
      sortAccessor: (r) => r.title,
    },
    {
      id: 'company',
      header: 'Company',
      cell: (r) => (r.company_id ? (companyById.get(r.company_id) ?? dash) : dash),
      sortAccessor: (r) => (r.company_id ? companyById.get(r.company_id) : undefined),
    },
    {
      id: 'email',
      header: 'Email',
      cell: (r) =>
        r.email ? (
          <a
            href={`mailto:${r.email}`}
            onClick={stop}
            className="text-primary hover:underline"
          >
            {r.email}
          </a>
        ) : (
          dash
        ),
    },
    {
      id: 'phone',
      header: 'Phone',
      cell: (r) =>
        r.phone ? (
          <a href={`tel:${r.phone}`} onClick={stop} className="hover:underline">
            {r.phone}
          </a>
        ) : (
          dash
        ),
    },
    {
      id: 'linkedin',
      header: 'LinkedIn',
      cell: (r) =>
        r.linkedin_url ? (
          <a
            href={r.linkedin_url}
            target="_blank"
            rel="noreferrer noopener"
            onClick={stop}
            className="inline-flex items-center gap-1 text-primary hover:underline"
          >
            Profile <ExternalLink className="h-3.5 w-3.5" />
          </a>
        ) : (
          dash
        ),
    },
    {
      id: 'actions',
      header: <span className="sr-only">Actions</span>,
      headerClassName: 'w-12',
      cell: (r) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              aria-label={`Actions for ${recruiterName(r)}`}
              onClick={stop}
            >
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => openEdit(r)}>
              <Pencil className="h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => setDeleting(r)}
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Recruiters"
        description="Keep recruiters and contacts organised."
        actions={
          <Button onClick={openCreate} title="Add recruiter (press c)">
            <Plus className="h-4 w-4" />
            Add recruiter
          </Button>
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <SearchBar
          value={query}
          onChange={handleSearch}
          placeholder="Search name, email, or title…"
          inputRef={searchInputRef}
          shortcutHint="/"
        />
        <Select value={companyFilter} onValueChange={handleCompanyFilter}>
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
      ) : (
        <>
          <DataTable
            columns={columns}
            data={recruiters}
            getRowId={(r) => r.id}
            isLoading={isLoading}
            skeletonRows={PAGE_SIZE}
            onRowClick={openEdit}
            emptyContent={
              <EmptyState
                icon={UserSquare2}
                title={hasFilters ? 'No recruiters match your filters' : 'No recruiters yet'}
                description={
                  hasFilters
                    ? 'Try a different search or company filter.'
                    : 'Add your first recruiter or contact.'
                }
                action={
                  !hasFilters ? (
                    <Button onClick={openCreate}>
                      <Plus className="h-4 w-4" />
                      Add recruiter
                    </Button>
                  ) : undefined
                }
              />
            }
          />

          {total > 0 ? (
            <Pagination
              skip={skip}
              limit={PAGE_SIZE}
              total={total}
              onPageChange={setSkip}
              className={isFetching ? 'opacity-70' : undefined}
            />
          ) : null}
        </>
      )}

      <RecruiterFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        recruiter={editing}
      />

      <ConfirmDeleteDialog
        open={Boolean(deleting)}
        onOpenChange={(open) => !open && setDeleting(null)}
        onConfirm={confirmDelete}
        resourceName={deleting ? recruiterName(deleting) : undefined}
        isPending={deleteRecruiter.isPending}
      />
    </div>
  );
}
