import {
  Building2,
  ExternalLink,
  MoreHorizontal,
  Pencil,
  Plus,
  Trash2,
} from 'lucide-react';
import { useRef, useState } from 'react';

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
import { CompanyFormDialog } from '@/features/companies/components/company-form-dialog';
import {
  useCompanies,
  useDeleteCompany,
} from '@/features/companies/hooks/use-companies';
import type { Company } from '@/features/companies/types/company.types';
import { getErrorMessage } from '@/lib/errors';
import { useHotkeys } from '@/hooks/use-hotkeys';
import { useToast } from '@/hooks/use-toast';
import { formatDate } from '@/utils/format';

const PAGE_SIZE = 10;

export function CompaniesPage() {
  const { toast } = useToast();

  const [query, setQuery] = useState('');
  const [skip, setSkip] = useState(0);

  // Dialog state: which company (if any) is being edited / deleted.
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Company | null>(null);
  const [deleting, setDeleting] = useState<Company | null>(null);

  const searchInputRef = useRef<HTMLInputElement>(null);

  // Keyboard shortcuts: "/" focuses search, "c" opens the create dialog.
  // Disabled while a dialog is open so it can't fire behind a modal.
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

  const { data, isLoading, isError, error, refetch, isFetching } = useCompanies({
    query: query || undefined,
    skip,
    limit: PAGE_SIZE,
  });

  const deleteCompany = useDeleteCompany();

  const companies = data?.items ?? [];
  const total = data?.total ?? 0;

  function handleSearch(value: string) {
    setQuery(value);
    setSkip(0); // Reset to first page on a new search.
  }

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(company: Company) {
    setEditing(company);
    setFormOpen(true);
  }

  function confirmDelete() {
    if (!deleting) return;
    deleteCompany.mutate(deleting.id, {
      onSuccess: () => {
        toast({ title: 'Company deleted', description: deleting.name });
        // If we deleted the last row on a page, step back a page.
        if (companies.length === 1 && skip > 0) setSkip((s) => Math.max(0, s - PAGE_SIZE));
        setDeleting(null);
      },
      onError: (err) =>
        toast({
          variant: 'destructive',
          title: 'Could not delete company',
          description: getErrorMessage(err),
        }),
    });
  }

  const columns: DataTableColumn<Company>[] = [
    {
      id: 'name',
      header: 'Name',
      cell: (c) => <span className="font-medium">{c.name}</span>,
      sortAccessor: (c) => c.name,
    },
    {
      id: 'industry',
      header: 'Industry',
      cell: (c) => c.industry ?? <span className="text-muted-foreground">—</span>,
      sortAccessor: (c) => c.industry,
    },
    {
      id: 'location',
      header: 'Location',
      cell: (c) => c.location ?? <span className="text-muted-foreground">—</span>,
      sortAccessor: (c) => c.location,
    },
    {
      id: 'website',
      header: 'Website',
      cell: (c) =>
        c.website ? (
          <a
            href={c.website}
            target="_blank"
            rel="noreferrer noopener"
            className="inline-flex items-center gap-1 text-primary hover:underline"
            onClick={(e) => e.stopPropagation()}
          >
            Visit <ExternalLink className="h-3.5 w-3.5" />
          </a>
        ) : (
          <span className="text-muted-foreground">—</span>
        ),
    },
    {
      id: 'created',
      header: 'Added',
      cell: (c) => (
        <span className="text-muted-foreground">{formatDate(c.created_at)}</span>
      ),
      // ISO timestamps sort lexicographically in chronological order.
      sortAccessor: (c) => c.created_at,
    },
    {
      id: 'actions',
      header: <span className="sr-only">Actions</span>,
      headerClassName: 'w-12',
      cell: (c) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              aria-label={`Actions for ${c.name}`}
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => openEdit(c)}>
              <Pencil className="h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => setDeleting(c)}
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
        title="Companies"
        description="Manage the companies you're applying to."
        actions={
          <Button onClick={openCreate} title="Add company (press c)">
            <Plus className="h-4 w-4" />
            Add company
          </Button>
        }
      />

      <div className="flex items-center justify-between gap-3">
        <SearchBar
          value={query}
          onChange={handleSearch}
          placeholder="Search companies…"
          inputRef={searchInputRef}
          shortcutHint="/"
        />
      </div>

      {isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : (
        <>
          <DataTable
            columns={columns}
            data={companies}
            getRowId={(c) => c.id}
            isLoading={isLoading}
            skeletonRows={PAGE_SIZE}
            onRowClick={openEdit}
            emptyContent={
              <EmptyState
                icon={Building2}
                title={query ? 'No companies match your search' : 'No companies yet'}
                description={
                  query
                    ? 'Try a different search term.'
                    : 'Add your first company to start tracking applications.'
                }
                action={
                  !query ? (
                    <Button onClick={openCreate}>
                      <Plus className="h-4 w-4" />
                      Add company
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

      <CompanyFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        company={editing}
      />

      <ConfirmDeleteDialog
        open={Boolean(deleting)}
        onOpenChange={(open) => !open && setDeleting(null)}
        onConfirm={confirmDelete}
        resourceName={deleting?.name}
        isPending={deleteCompany.isPending}
      />
    </div>
  );
}
