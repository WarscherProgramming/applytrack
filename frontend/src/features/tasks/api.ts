import { apiClient } from '@/services/api-client';
import type { PaginatedResponse } from '@/types/api';

import type {
  Task,
  TaskCreateInput,
  TaskGenerationResponse,
  TaskListParams,
  TaskUpdateInput,
} from './types';

export const tasksApi = {
  list(params: TaskListParams = {}): Promise<PaginatedResponse<Task>> {
    return apiClient
      .get<PaginatedResponse<Task>>('/tasks/', { params })
      .then((res) => res.data);
  },

  create(input: TaskCreateInput): Promise<Task> {
    return apiClient.post<Task>('/tasks/', input).then((res) => res.data);
  },

  update(id: string, input: TaskUpdateInput): Promise<Task> {
    return apiClient.patch<Task>(`/tasks/${id}`, input).then((res) => res.data);
  },

  complete(id: string): Promise<Task> {
    return apiClient.post<Task>(`/tasks/${id}/complete`).then((res) => res.data);
  },

  dismiss(id: string): Promise<Task> {
    return apiClient.post<Task>(`/tasks/${id}/dismiss`).then((res) => res.data);
  },

  remove(id: string): Promise<void> {
    return apiClient.delete(`/tasks/${id}`).then(() => undefined);
  },

  generateAll(): Promise<TaskGenerationResponse> {
    return apiClient
      .post<TaskGenerationResponse>('/tasks/generate/all')
      .then((res) => res.data);
  },
};
