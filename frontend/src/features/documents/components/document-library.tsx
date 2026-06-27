import { Plus } from 'lucide-react';
import { useMemo, useState } from 'react';

import { ConfirmDeleteDialog } from '@/components/common/confirm-delete-dialog';
import { EmptyState } from '@/components/common/empty-state';
import { ErrorState } from '@/components/common/error-state';
import { PageHeader } from '@/components/common/page-header';
import { Pagination } from '@/components/common/pagination';
import { SearchBar } from '@/components/common/search-bar';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';

import type { DocumentConfig } from '../config';
import { groupDocuments } from '../lib';
import type { DocumentGroup, DocumentItem } from '../types';
import { DocumentGroupCard } from './document-group-card';
import { DocumentRenameDialog } from './document-rename-dialog';
import { DocumentUploadDialog } from './document-upload-dialog';

const PAGE_SIZE = 50;

interface DocumentLibraryProps {
  config: DocumentConfig;
}

/**
 * The shared library UI for a document resource (resumes or cover letters):
 * search, grouped version cards, upload, rename, version history, download,
 * and delete. All resource-specific behaviour comes from `config`.
 */
export function DocumentLibrary({ config }: DocumentLibraryProps) {
  const { noun, nounPlural, title, description, icon: Icon } = config;
  const { toast } = useToast();

  const [query, setQuery] = useState('');
  const [skip, setSkip] = useState(0);

  // null preset = new document; string preset = new version of that document.
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadPreset, setUploadPreset] = useState<string | null>(null);
  const [renaming, setRenaming] = useState<DocumentGroup | null>(null);
  const [deletingGroup, setDeletingGroup] = useState<DocumentGroup | null>(null);
  const [deletingVersion, setDeletingVersion] = useState<DocumentItem | null>(null);

  const { data, isLoading, isError, error, refetch, isFetching } =
    config.hooks.useDocuments({
      query: query || undefined,
      skip,
      limit: PAGE_SIZE,
    });

  const deleteVersion = config.hooks.useDeleteDocument();
  const deleteGroup = config.hooks.useDeleteDocumentGroup();

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const groups = useMemo(() => groupDocuments(items), [items]);

  function handleSearch(value: string) {
    setQuery(value);
    setSkip(0);
  }

  function openNewDocument() {
    setUploadPreset(null);
    setUploadOpen(true);
  }

  function openNewVersion(name: string) {
    setUploadPreset(name);
    setUploadOpen(true);
  }

  function confirmDeleteVersion() {
    if (!deletingVersion) return;
    deleteVersion.mutate(deletingVersion.id, {
      onSuccess: () => {
        toast({
          title: 'Version deleted',
          description: `${deletingVersion.name} · v${deletingVersion.version}`,
        });
        setDeletingVersion(null);
      },
      onError: (err) =>
        toast({
          variant: 'destructive',
          title: 'Could not delete version',
          description: getErrorMessage(err),
        }),
    });
  }

  function confirmDeleteGroup() {
    if (!deletingGroup) return;
    deleteGroup.mutate(
      deletingGroup.versions.map((v) => v.id),
      {
        onSuccess: () => {
          toast({ title: `${noun} deleted`, description: deletingGroup.name });
          if (groups.length === 1 && skip > 0) {
            setSkip((s) => Math.max(0, s - PAGE_SIZE));
          }
          setDeletingGroup(null);
        },
        onError: (err) =>
          toast({
            variant: 'destructive',
            title: `Could not delete ${noun}`,
            description: getErrorMessage(err),
          }),
      },
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={title}
        description={description}
        actions={
          <Button onClick={openNewDocument}>
            <Plus className="h-4 w-4" />
            Upload {noun}
          </Button>
        }
      />

      <SearchBar
        value={query}
        onChange={handleSearch}
        placeholder={`Search ${nounPlural}…`}
      />

      {isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-5">
                <Skeleton className="h-5 w-48" />
                <Skeleton className="mt-2 h-4 w-64" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : groups.length === 0 ? (
        <EmptyState
          icon={Icon}
          title={query ? `No ${nounPlural} match your search` : `No ${nounPlural} yet`}
          description={
            query
              ? 'Try a different search term.'
              : `Upload your first ${noun} to start tracking versions.`
          }
          action={
            !query ? (
              <Button onClick={openNewDocument}>
                <Plus className="h-4 w-4" />
                Upload {noun}
              </Button>
            ) : undefined
          }
        />
      ) : (
        <>
          <div className={cnFetching(isFetching)}>
            <div className="space-y-3">
              {groups.map((group) => (
                <DocumentGroupCard
                  key={group.name}
                  group={group}
                  config={config}
                  onUploadVersion={openNewVersion}
                  onRename={setRenaming}
                  onDeleteGroup={setDeletingGroup}
                  onDeleteVersion={setDeletingVersion}
                />
              ))}
            </div>
          </div>

          {total > PAGE_SIZE ? (
            <Pagination
              skip={skip}
              limit={PAGE_SIZE}
              total={total}
              onPageChange={setSkip}
            />
          ) : null}
        </>
      )}

      <DocumentUploadDialog
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        config={config}
        presetName={uploadPreset}
      />

      <DocumentRenameDialog
        open={Boolean(renaming)}
        onOpenChange={(open) => !open && setRenaming(null)}
        config={config}
        group={renaming}
      />

      <ConfirmDeleteDialog
        open={Boolean(deletingGroup)}
        onOpenChange={(open) => !open && setDeletingGroup(null)}
        onConfirm={confirmDeleteGroup}
        title={`Delete ${noun}`}
        resourceName={deletingGroup?.name}
        description={
          deletingGroup && deletingGroup.versions.length > 1 ? (
            <>
              This deletes all {deletingGroup.versions.length} versions of{' '}
              <span className="font-medium text-foreground">
                {deletingGroup.name}
              </span>
              . This action cannot be undone.
            </>
          ) : undefined
        }
        isPending={deleteGroup.isPending}
      />

      <ConfirmDeleteDialog
        open={Boolean(deletingVersion)}
        onOpenChange={(open) => !open && setDeletingVersion(null)}
        onConfirm={confirmDeleteVersion}
        title="Delete version"
        resourceName={
          deletingVersion
            ? `${deletingVersion.name} · v${deletingVersion.version}`
            : undefined
        }
        isPending={deleteVersion.isPending}
      />
    </div>
  );
}

/** Dim the list while a background refetch is in flight. */
function cnFetching(isFetching: boolean): string {
  return isFetching ? 'opacity-70 transition-opacity' : '';
}
