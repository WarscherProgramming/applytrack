interface StringListProps {
  items: string[];
  emptyText?: string;
}

/** Bulleted list of strings with an empty-state fallback. */
export function StringList({ items, emptyText = 'None' }: StringListProps) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyText}</p>;
  }
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex gap-2 text-sm text-muted-foreground">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/40" />
          {item}
        </li>
      ))}
    </ul>
  );
}
