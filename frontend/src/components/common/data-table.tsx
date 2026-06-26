import { ArrowDown, ArrowUp, ChevronsUpDown } from 'lucide-react';
import { useMemo, useState, type ReactNode } from 'react';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

export interface DataTableColumn<T> {
  /** Stable key for the column. */
  id: string;
  header: ReactNode;
  /** Render the cell for a given row. */
  cell: (row: T) => ReactNode;
  className?: string;
  headerClassName?: string;
  /**
   * When provided, the column becomes sortable. Returns the comparable value
   * for a row (string/number). Sorting is applied to the rows currently passed
   * to the table (i.e. the current page).
   */
  sortAccessor?: (row: T) => string | number | null | undefined;
}

type SortDirection = 'asc' | 'desc';

interface SortState {
  columnId: string;
  direction: SortDirection;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  /** Extract a stable React key per row. */
  getRowId: (row: T) => string;
  isLoading?: boolean;
  /** Rows of skeletons to render while loading. */
  skeletonRows?: number;
  /** Shown when not loading and data is empty (e.g. an <EmptyState />). */
  emptyContent?: ReactNode;
  onRowClick?: (row: T) => void;
  className?: string;
}

/** Null/undefined always sort to the bottom regardless of direction. */
function compareValues(
  a: string | number | null | undefined,
  b: string | number | null | undefined,
): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  return String(a).localeCompare(String(b), undefined, { sensitivity: 'base' });
}

/**
 * Presentational, generically-typed table.
 *
 * Owns layout, loading skeletons, and optional client-side sorting (opt-in per
 * column via `sortAccessor`). Data fetching, empty/error states, and pagination
 * are composed by the page so the table stays reusable across every resource.
 */
export function DataTable<T>({
  columns,
  data,
  getRowId,
  isLoading = false,
  skeletonRows = 5,
  emptyContent,
  onRowClick,
  className,
}: DataTableProps<T>) {
  const [sort, setSort] = useState<SortState | null>(null);

  const sortedData = useMemo(() => {
    if (!sort) return data;
    const column = columns.find((c) => c.id === sort.columnId);
    if (!column?.sortAccessor) return data;
    const accessor = column.sortAccessor;
    // Copy before sorting so we never mutate the query cache's array.
    const next = [...data].sort((a, b) =>
      compareValues(accessor(a), accessor(b)),
    );
    return sort.direction === 'desc' ? next.reverse() : next;
  }, [data, sort, columns]);

  function toggleSort(columnId: string) {
    setSort((prev) => {
      if (prev?.columnId !== columnId) return { columnId, direction: 'asc' };
      if (prev.direction === 'asc') return { columnId, direction: 'desc' };
      return null; // Third click clears sorting, restoring server order.
    });
  }

  if (!isLoading && data.length === 0 && emptyContent) {
    return <>{emptyContent}</>;
  }

  return (
    <div className={cn('rounded-lg border', className)}>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            {columns.map((col) => {
              const isSortable = Boolean(col.sortAccessor);
              const active = sort?.columnId === col.id;
              return (
                <TableHead
                  key={col.id}
                  className={col.headerClassName}
                  aria-sort={
                    active
                      ? sort?.direction === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : undefined
                  }
                >
                  {isSortable ? (
                    <button
                      type="button"
                      onClick={() => toggleSort(col.id)}
                      className="-ml-1 inline-flex items-center gap-1 rounded px-1 py-0.5 font-medium uppercase tracking-wide text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      {col.header}
                      {active ? (
                        sort?.direction === 'asc' ? (
                          <ArrowUp className="h-3.5 w-3.5" />
                        ) : (
                          <ArrowDown className="h-3.5 w-3.5" />
                        )
                      ) : (
                        <ChevronsUpDown className="h-3.5 w-3.5 opacity-50" />
                      )}
                    </button>
                  ) : (
                    col.header
                  )}
                </TableHead>
              );
            })}
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading
            ? Array.from({ length: skeletonRows }).map((_, rowIdx) => (
                <TableRow key={`skeleton-${rowIdx}`} className="hover:bg-transparent">
                  {columns.map((col) => (
                    <TableCell key={col.id} className={col.className}>
                      <Skeleton className="h-5 w-full max-w-[160px]" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            : sortedData.map((row) => (
                <TableRow
                  key={getRowId(row)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={cn(onRowClick && 'cursor-pointer')}
                >
                  {columns.map((col) => (
                    <TableCell key={col.id} className={col.className}>
                      {col.cell(row)}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
        </TableBody>
      </Table>
    </div>
  );
}
