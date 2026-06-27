import type { InterviewPrepPackage, InterviewPrepResult } from './types';

function section(title: string, items: string[]): string {
  return items.length
    ? `## ${title}\n${items.map((i) => `- ${i}`).join('\n')}\n`
    : '';
}

/** Render a full prep package as Markdown for copy / download. */
export function packageToMarkdown(pkg: InterviewPrepPackage): string {
  const r: InterviewPrepResult = pkg.result;
  const o = r.company_overview;
  const q = r.likely_questions;
  const s = r.study_topics;
  const f = r.red_flags;

  const star = r.star_examples
    .map(
      (ex) =>
        `### ${ex.question}\n- **Situation:** ${ex.situation}\n- **Task:** ${ex.task}\n- **Action:** ${ex.action}\n- **Result:** ${ex.result}\n`,
    )
    .join('\n');

  return [
    `# Interview Prep — ${pkg.company_name} · ${pkg.job_title}`,
    pkg.interview_type ? `_${pkg.interview_type}${pkg.interview_round ? ` · ${pkg.interview_round}` : ''}_` : '',
    '',
    '## Company Overview',
    `**Mission:** ${o.mission}`,
    `**Industry:** ${o.industry}`,
    `**Culture:** ${o.culture}`,
    section('Products & Services', o.products_services),
    `**Recent news:** ${o.recent_news}`,
    '',
    section('Behavioral Questions', q.behavioral),
    section('Technical Questions', q.technical),
    section('Role-Specific Questions', q.role_specific),
    section('Company-Specific Questions', q.company_specific),
    star ? `## STAR Examples\n${star}` : '',
    section('Languages', s.languages),
    section('Frameworks', s.frameworks),
    section('Concepts', s.concepts),
    section('System Design', s.system_design),
    section('Algorithms', s.algorithms),
    section('Role-Specific Study', s.role_specific),
    section('Questions to Ask', r.questions_to_ask),
    section('Missing Resume Coverage', f.missing_resume_coverage),
    section('Skill Gaps', f.skill_gaps),
    section('Likely Challenges', f.likely_challenges),
    section('Checklist', r.checklist),
  ]
    .filter(Boolean)
    .join('\n')
    .trim();
}

export function slugify(value: string): string {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 60) || 'interview-prep'
  );
}

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

const PDF_STYLES = `
  body { font-family: ui-sans-serif, system-ui, sans-serif; line-height: 1.5; padding: 2rem; max-width: 48rem; margin: 0 auto; color: #111; }
  h1 { font-size: 1.5rem; } h2 { font-size: 1.15rem; margin-top: 1.5rem; border-bottom: 1px solid #ddd; padding-bottom: .25rem; }
  h3 { font-size: 1rem; margin-top: 1rem; } ul { margin: .25rem 0 .75rem 1.25rem; } em { color: #555; }
`;

/**
 * Export a package as PDF via the browser's print dialog.
 *
 * Deliberately dependency-free: we open a print-friendly window and call
 * print(), letting the user "Save as PDF". This avoids bundling a PDF library
 * while still producing a genuine PDF.
 */
export function exportPackagePdf(pkg: InterviewPrepPackage): void {
  const html = markdownToHtml(packageToMarkdown(pkg));
  const win = window.open('', '_blank', 'width=820,height=900');
  if (!win) return;
  win.document.write(
    `<!doctype html><html><head><title>${pkg.company_name} — Interview Prep</title>` +
      `<style>${PDF_STYLES}</style></head><body>${html}</body></html>`,
  );
  win.document.close();
  win.focus();
  // Give the new document a tick to lay out before printing.
  setTimeout(() => win.print(), 250);
}

/** Minimal Markdown → HTML for the print view (headings, bullets, bold). */
function markdownToHtml(md: string): string {
  const escape = (s: string) =>
    s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const lines = md.split('\n');
  const out: string[] = [];
  let inList = false;
  const closeList = () => {
    if (inList) {
      out.push('</ul>');
      inList = false;
    }
  };
  for (const raw of lines) {
    const line = raw.trimEnd();
    const bold = (t: string) =>
      escape(t).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    if (line.startsWith('### ')) {
      closeList();
      out.push(`<h3>${bold(line.slice(4))}</h3>`);
    } else if (line.startsWith('## ')) {
      closeList();
      out.push(`<h2>${bold(line.slice(3))}</h2>`);
    } else if (line.startsWith('# ')) {
      closeList();
      out.push(`<h1>${bold(line.slice(2))}</h1>`);
    } else if (line.startsWith('- ')) {
      if (!inList) {
        out.push('<ul>');
        inList = true;
      }
      out.push(`<li>${bold(line.slice(2))}</li>`);
    } else if (line.startsWith('_') && line.endsWith('_') && line.length > 1) {
      closeList();
      out.push(`<p><em>${bold(line.slice(1, -1))}</em></p>`);
    } else if (line) {
      closeList();
      out.push(`<p>${bold(line)}</p>`);
    }
  }
  closeList();
  return out.join('\n');
}
