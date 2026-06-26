/** Shared shapes that mirror the backend's response contracts. */

/** Every list endpoint returns this envelope (items + pagination metadata). */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

/** Common pagination query parameters accepted by list endpoints. */
export interface PaginationParams {
  skip?: number;
  limit?: number;
}

/** Fields present on every persisted entity (see EntitySchema on the backend). */
export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at: string;
}
