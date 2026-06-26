import { Badge, type BadgeProps } from '@/components/ui/badge';
import { humanizeEnum } from '@/utils/format';

type BadgeVariant = NonNullable<BadgeProps['variant']>;

/**
 * Maps every backend status value (across applications, interviews, and
 * follow-ups) to a semantic badge colour. Centralised so status colours stay
 * consistent everywhere they appear.
 */
const STATUS_VARIANTS: Record<string, BadgeVariant> = {
  // Applications
  draft: 'secondary',
  applied: 'default',
  assessment: 'warning',
  phone_screen: 'warning',
  interview: 'warning',
  final_interview: 'warning',
  offer: 'success',
  accepted: 'success',
  rejected: 'destructive',
  withdrawn: 'secondary',
  ghosted: 'secondary',
  // Interviews
  scheduled: 'default',
  completed: 'success',
  cancelled: 'destructive',
  rescheduled: 'warning',
  no_show: 'destructive',
  // Follow-ups
  pending: 'warning',
  skipped: 'secondary',
};

interface StatusBadgeProps {
  status: string;
  className?: string;
}

/** Coloured badge for any resource status. */
export function StatusBadge({ status, className }: StatusBadgeProps) {
  const variant = STATUS_VARIANTS[status] ?? 'outline';
  return (
    <Badge variant={variant} className={className}>
      {humanizeEnum(status)}
    </Badge>
  );
}
