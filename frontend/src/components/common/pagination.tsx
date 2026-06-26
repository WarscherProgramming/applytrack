import { ChevronLeft, ChevronRight } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface PaginationProps {
  /** Zero-based offset of the first item on the current page. */
  skip: number;
  /** Page size. */
  limit: number;
  /** Total number of records across all pages. */
  total: number;
  onPageChange: (nextSkip: number) => void;
  className?: string;
}

/**
 * Offset-based pagination control matching the backend's skip/limit contract.
 * Shows the current record range and Prev/Next navigation.
 */
export function Pagination({
  skip,
  limit,
  total,
  onPageChange,
  className,
}: PaginationProps) {
  const currentPage = Math.floor(skip / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const firstItem = total === 0 ? 0 : skip + 1;
  const lastItem = Math.min(skip + limit, total);

  const canPrev = skip > 0;
  const canNext = skip + limit < total;

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-between gap-3 sm:flex-row',
        className,
      )}
    >
      <p className="text-sm text-muted-foreground">
        {total === 0 ? (
          'No results'
        ) : (
          <>
            Showing <span className="font-medium text-foreground">{firstItem}</span>
            –<span className="font-medium text-foreground">{lastItem}</span> of{' '}
            <span className="font-medium text-foreground">{total}</span>
          </>
        )}
      </p>

      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">
          Page {currentPage} of {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={!canPrev}
          onClick={() => onPageChange(Math.max(0, skip - limit))}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
          Prev
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={!canNext}
          onClick={() => onPageChange(skip + limit)}
          aria-label="Next page"
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
