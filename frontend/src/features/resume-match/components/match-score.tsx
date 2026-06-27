import { cn } from '@/lib/utils';

import { scoreBand } from '../lib';

interface MatchScoreProps {
  score: number;
  size?: number;
}

const RING_CLASS = {
  strong: 'stroke-success',
  moderate: 'stroke-warning',
  weak: 'stroke-destructive',
} as const;

const TEXT_CLASS = {
  strong: 'text-success',
  moderate: 'text-warning',
  weak: 'text-destructive',
} as const;

const LABEL = {
  strong: 'Strong match',
  moderate: 'Moderate match',
  weak: 'Weak match',
} as const;

/** Circular gauge rendering the 0–100 overall match score. */
export function MatchScore({ score, size = 132 }: MatchScoreProps) {
  const band = scoreBand(score);
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference * (1 - clamped / 100);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            strokeWidth={stroke}
            className="fill-none stroke-muted"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className={cn('fill-none transition-all', RING_CLASS[band])}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn('text-3xl font-bold tabular-nums', TEXT_CLASS[band])}>
            {clamped}
          </span>
          <span className="text-xs text-muted-foreground">/ 100</span>
        </div>
      </div>
      <span className={cn('text-sm font-medium', TEXT_CLASS[band])}>
        {LABEL[band]}
      </span>
    </div>
  );
}
