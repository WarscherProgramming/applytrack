import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { useMemo } from 'react';

import type { DocumentApi } from './api';
import type {
  DocumentItem,
  DocumentListParams,
  DocumentUpdateInput,
  DocumentUploadInput,
} from './types';

const EMPTY: DocumentItem[] = [];

/** A selectable document version for the application form pickers. */
export interface DocumentOption {
  id: string;
  /** e.g. "Backend Resume · v3". */
  label: string;
}

/**
 * Build a TanStack Query hook set + key factory for one document resource.
 * Resumes and cover letters get independent caches via a distinct resourceKey
 * (e.g. "resumes", "cover-letters"), but share this implementation.
 */
export function createDocumentHooks(resourceKey: string, api: DocumentApi) {
  const keys = {
    all: [resourceKey] as const,
    lists: () => [...keys.all, 'list'] as const,
    list: (params: DocumentListParams) => [...keys.lists(), params] as const,
    options: () => [...keys.all, 'options'] as const,
    details: () => [...keys.all, 'detail'] as const,
    detail: (id: string) => [...keys.details(), id] as const,
  };

  function useDocuments(params: DocumentListParams) {
    return useQuery({
      queryKey: keys.list(params),
      queryFn: () => api.list(params),
      placeholderData: keepPreviousData,
    });
  }

  function useUploadDocument() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: (input: DocumentUploadInput) => api.upload(input),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: keys.all });
      },
    });
  }

  function useUpdateDocument() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ id, input }: { id: string; input: DocumentUpdateInput }) =>
        api.update(id, input),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: keys.all });
      },
    });
  }

  function useDeleteDocument() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: (id: string) => api.remove(id),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: keys.all });
      },
    });
  }

  /**
   * Rename a logical document: versions share a name, so renaming applies the
   * new name to every version id in the group in one mutation.
   */
  function useRenameDocument() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ ids, name }: { ids: string[]; name: string }) =>
        Promise.all(ids.map((id) => api.update(id, { name }))),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: keys.all });
      },
    });
  }

  /** Delete an entire document and all of its versions. */
  function useDeleteDocumentGroup() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: (ids: string[]) => Promise.all(ids.map((id) => api.remove(id))),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: keys.all });
      },
    });
  }

  /**
   * Load every version (capped at the backend's 100 max) for selection in the
   * application form. Returns ready-to-render options plus an id→option lookup
   * so a stored selection can be labelled without an extra fetch.
   */
  function useDocumentOptions() {
    const query = useQuery({
      queryKey: keys.options(),
      queryFn: () => api.list({ skip: 0, limit: 100 }),
    });

    const items = query.data?.items ?? EMPTY;

    const options = useMemo<DocumentOption[]>(
      () =>
        items.map((doc) => ({ id: doc.id, label: `${doc.name} · v${doc.version}` })),
      [items],
    );

    const byId = useMemo(() => {
      const map = new Map<string, DocumentOption>();
      for (const opt of options) map.set(opt.id, opt);
      return map;
    }, [options]);

    return { ...query, options, byId };
  }

  return {
    keys,
    useDocuments,
    useUploadDocument,
    useUpdateDocument,
    useDeleteDocument,
    useRenameDocument,
    useDeleteDocumentGroup,
    useDocumentOptions,
  };
}

export type DocumentHooks = ReturnType<typeof createDocumentHooks>;
