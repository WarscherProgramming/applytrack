import { Search, X } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

interface SearchBarProps {
  /** Controlled value (the committed/debounced search term). */
  value: string;
  /** Fires after the debounce interval with the new term. */
  onChange: (value: string) => void;
  placeholder?: string;
  /** Debounce delay in ms; set 0 to fire on every keystroke. */
  debounceMs?: number;
  className?: string;
}

/**
 * Debounced search input. Keeps its own immediate text state for a responsive
 * field, and only calls onChange after the user pauses typing — avoiding a
 * network request per keystroke.
 */
export function SearchBar({
  value,
  onChange,
  placeholder = 'Search…',
  debounceMs = 300,
  className,
}: SearchBarProps) {
  const [text, setText] = useState(value);

  // Keep local text in sync when the parent resets the value externally.
  useEffect(() => {
    setText(value);
  }, [value]);

  useEffect(() => {
    if (text === value) return;
    const handle = setTimeout(() => onChange(text), debounceMs);
    return () => clearTimeout(handle);
    // onChange is intentionally omitted; callers pass stable setters.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, debounceMs]);

  return (
    <div className={cn('relative w-full sm:max-w-xs', className)}>
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        type="search"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
        className="pl-9 pr-9 [&::-webkit-search-cancel-button]:appearance-none"
      />
      {text ? (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Clear search"
          onClick={() => {
            setText('');
            onChange('');
          }}
          className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2 text-muted-foreground"
        >
          <X className="h-4 w-4" />
        </Button>
      ) : null}
    </div>
  );
}
