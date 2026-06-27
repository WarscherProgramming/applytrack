import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

import type {
  DocumentItem,
  DocumentListParams,
  DocumentUpdateInput,
  DocumentUploadInput,
} from './types';

/**
 * A typed client for one document resource. Resumes and cover letters expose
 * identical REST surfaces, so the client is generated from a base path
 * (e.g. "/resumes", "/cover-letters") rather than duplicated per feature.
 */
export interface DocumentApi {
  list(params?: DocumentListParams): Promise<PaginatedResponse<DocumentItem>>;
  get(id: string): Promise<DocumentItem>;
  upload(input: DocumentUploadInput): Promise<DocumentItem>;
  update(id: string, input: DocumentUpdateInput): Promise<DocumentItem>;
  remove(id: string): Promise<void>;
  /** Absolute URL of the binary download endpoint (for anchor-based saves). */
  downloadUrl(id: string): string;
}

export function createDocumentApi(basePath: string): DocumentApi {
  // basePath has no trailing slash; collection routes append "/".
  return {
    list(params = {}) {
      return apiClient
        .get<PaginatedResponse<DocumentItem>>(`${basePath}/`, { params })
        .then((res) => res.data);
    },

    get(id) {
      return apiClient
        .get<DocumentItem>(`${basePath}/${id}`)
        .then((res) => res.data);
    },

    upload({ file, name, notes }) {
      const form = new FormData();
      form.append('file', file);
      if (name) form.append('name', name);
      if (notes) form.append('notes', notes);
      // Let axios set the multipart boundary by overriding the JSON default.
      return apiClient
        .post<DocumentItem>(`${basePath}/`, form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        .then((res) => res.data);
    },

    update(id, input) {
      return apiClient
        .patch<DocumentItem>(`${basePath}/${id}`, input)
        .then((res) => res.data);
    },

    remove(id) {
      return apiClient.delete(`${basePath}/${id}`).then(() => undefined);
    },

    downloadUrl(id) {
      const base = apiClient.defaults.baseURL ?? '';
      return `${base}${basePath}/${id}/download`;
    },
  };
}
