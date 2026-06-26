import { Badge, type BadgeProps } from '@/components/ui/badge';
import { humanizeEnum } from '@/utils/format';

type BadgeVariant = NonNullable<BadgeProps['variant']>;

/** Follow-up priority → badge colour. */
const PRIORITY_VARIANTS: Record<string, BadgeVariant> = {
  low: 'secondary',
  medium: 'default',
  high: 'warning',
  urgent: 'destructive',
};

interface PriorityBadgeProps {
  priority: string;
  className?: string;
}

/** Coloured badge representing a follow-up's priority. */
export function PriorityBadge({ priority, className }: PriorityBadgeProps) {
  const variant = PRIORITY_VARIANTS[priority] ?? 'outline';
  return (
    <Badge variant={variant} className={className}>
      {humanizeEnum(priority)}
    </Badge>
  );
}
