import type { ResumeMatchAnalysis, ResumeMatchResult } from './types';

/** Visual band for a match score, used to colour the score and badges. */
export type ScoreBand = 'strong' | 'moderate' | 'weak';

export function scoreBand(score: number): ScoreBand {
  if (score >= 75) return 'strong';
  if (score >= 50) return 'moderate';
  return 'weak';
}

const BAND_CLASSES: Record<ScoreBand, string> = {
  strong: 'text-success',
  moderate: 'text-warning',
  weak: 'text-destructive',
};

export function scoreColorClass(score: number): string {
  return BAND_CLASSES[scoreBand(score)];
}

/** Render an analysis as Markdown for copy/export. */
export function analysisToMarkdown(analysis: ResumeMatchAnalysis): string {
  const r: ResumeMatchResult = analysis.result;
  const section = (title: string, items: string[]): string =>
    items.length
      ? `## ${title}\n${items.map((i) => `- ${i}`).join('\n')}\n`
      : '';

  return [
    `# Resume Match — ${analysis.resume_name}`,
    `**Overall match score:** ${analysis.overall_match_score}/100`,
    '',
    section('Strengths', r.strengths),
    section('Weaknesses', r.weaknesses),
    section('Missing skills', r.missing_skills),
    section('Recommended keywords', r.recommended_keywords),
    section('Recommended resume changes', r.recommended_resume_changes),
    section('Interview topics', r.interview_topics),
  ]
    .filter(Boolean)
    .join('\n')
    .trim();
}

/** Trigger a client-side download of `content` as a file. */
export function downloadTextFile(
  fileName: string,
  content: string,
  mimeType = 'text/markdown',
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

/** A filesystem-safe slug for export filenames. */
export function slugify(value: string): string {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 60) || 'resume-match'
  );
}
