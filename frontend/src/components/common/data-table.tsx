import type { ReactNode } from 'react';

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

/**
 * Presentational, generically-typed table.
 *
 * Owns only layout + loading skeletons. Data fetching, empty/error states, and
 * pagination are composed by the page so the table stays reusable across every
 * resource.
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
  if (!isLoading && data.length === 0 && emptyContent) {
    return <>{emptyContent}</>;
  }

  return (
    <div className={cn('rounded-lg border', className)}>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            {columns.map((col) => (
              <TableHead key={col.id} className={col.headerClassName}>
                {col.header}
              </TableHead>
            ))}
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
            : data.map((row) => (
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
