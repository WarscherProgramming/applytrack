import {
  Building2,
  Copy,
  FileDown,
  GraduationCap,
  HelpCircle,
  ListChecks,
  MessageSquareQuote,
  RefreshCw,
  TriangleAlert,
} from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { getErrorMessage } from '@/lib/errors';
import { formatDateTime } from '@/utils/format';
import { useToast } from '@/hooks/use-toast';

import {
  downloadTextFile,
  exportPackagePdf,
  packageToMarkdown,
  slugify,
} from '../lib';
import type { InterviewPrepPackage } from '../types';
import { CollapsibleSection } from './collapsible-section';
import { StringList } from './string-list';
import { UsageSummary } from './usage-summary';

interface PrepResultProps {
  package: InterviewPrepPackage;
  isRegenerating: boolean;
  onRegenerate: () => void;
}

function OverviewCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-muted/30 p-3">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-sm">{value || '—'}</p>
    </div>
  );
}

function SubList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-1.5">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      <StringList items={items} />
    </div>
  );
}

export function PrepResult({
  package: pkg,
  isRegenerating,
  onRegenerate,
}: PrepResultProps) {
  const { toast } = useToast();
  const r = pkg.result;
  const [checked, setChecked] = useState<Set<number>>(new Set());

  function toggle(i: number) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(i)) {
        next.delete(i);
      } else {
        next.add(i);
      }
      return next;
    });
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(packageToMarkdown(pkg));
      toast({ title: 'Copied to clipboard' });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Could not copy',
        description: getErrorMessage(error),
      });
    }
  }

  function handleDownload() {
    downloadTextFile(
      `${slugify(`${pkg.company_name}-${pkg.job_title}`)}-prep.md`,
      packageToMarkdown(pkg),
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <CardTitle>
              {pkg.company_name} · {pkg.job_title}
            </CardTitle>
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              {pkg.interview_type ? (
                <Badge variant="secondary">{pkg.interview_type}</Badge>
              ) : null}
              {pkg.interview_round ? (
                <Badge variant="outline">{pkg.interview_round}</Badge>
              ) : null}
              <span>{formatDateTime(pkg.created_at)}</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={handleCopy}>
              <Copy className="h-4 w-4" />
              Copy
            </Button>
            <Button variant="outline" size="sm" onClick={() => exportPackagePdf(pkg)}>
              <FileDown className="h-4 w-4" />
              Export PDF
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <FileDown className="h-4 w-4" />
              .md
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onRegenerate}
              disabled={isRegenerating}
            >
              <RefreshCw
                className={cn('h-4 w-4', isRegenerating && 'animate-spin')}
              />
              Regenerate
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <UsageSummary usage={pkg.usage} />

          {/* Company overview cards */}
          <section className="space-y-3">
            <h3 className="flex items-center gap-2 text-sm font-semibold">
              <Building2 className="h-4 w-4 text-primary" />
              Company overview
            </h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <OverviewCard label="Mission" value={r.company_overview.mission} />
              <OverviewCard label="Industry" value={r.company_overview.industry} />
              <OverviewCard label="Culture" value={r.company_overview.culture} />
              <OverviewCard
                label="Recent news"
                value={r.company_overview.recent_news}
              />
            </div>
            {r.company_overview.products_services.length ? (
              <div className="flex flex-wrap gap-2">
                {r.company_overview.products_services.map((p, i) => (
                  <Badge key={i} variant="secondary">
                    {p}
                  </Badge>
                ))}
              </div>
            ) : null}
          </section>
        </CardContent>
      </Card>

      {/* Accordion sections */}
      <CollapsibleSection
        icon={MessageSquareQuote}
        title="Likely interview questions"
        defaultOpen
      >
        <div className="space-y-4">
          <SubList title="Behavioral" items={r.likely_questions.behavioral} />
          <SubList title="Technical" items={r.likely_questions.technical} />
          <SubList title="Role-specific" items={r.likely_questions.role_specific} />
          <SubList
            title="Company-specific"
            items={r.likely_questions.company_specific}
          />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        icon={MessageSquareQuote}
        title="STAR response coaching"
        count={r.star_examples.length}
      >
        <div className="space-y-4">
          {r.star_examples.length === 0 ? (
            <p className="text-sm text-muted-foreground">No examples generated.</p>
          ) : (
            r.star_examples.map((ex, i) => (
              <div key={i} className="rounded-lg border bg-muted/20 p-3">
                <p className="mb-2 text-sm font-medium">{ex.question}</p>
                <dl className="space-y-1 text-sm text-muted-foreground">
                  {(
                    [
                      ['Situation', ex.situation],
                      ['Task', ex.task],
                      ['Action', ex.action],
                      ['Result', ex.result],
                    ] as const
                  ).map(([label, value]) => (
                    <div key={label} className="flex gap-2">
                      <dt className="w-20 shrink-0 font-medium text-foreground">
                        {label}
                      </dt>
                      <dd>{value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))
          )}
        </div>
      </CollapsibleSection>

      <CollapsibleSection icon={GraduationCap} title="Technical study topics">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <SubList title="Languages" items={r.study_topics.languages} />
          <SubList title="Frameworks" items={r.study_topics.frameworks} />
          <SubList title="Concepts" items={r.study_topics.concepts} />
          <SubList title="System design" items={r.study_topics.system_design} />
          <SubList title="Algorithms" items={r.study_topics.algorithms} />
          <SubList title="Role-specific" items={r.study_topics.role_specific} />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        icon={HelpCircle}
        title="Questions to ask the interviewer"
        count={r.questions_to_ask.length}
      >
        <StringList items={r.questions_to_ask} />
      </CollapsibleSection>

      <CollapsibleSection icon={TriangleAlert} title="Red flags & gaps">
        <div className="space-y-4">
          <SubList
            title="Missing resume coverage"
            items={r.red_flags.missing_resume_coverage}
          />
          <SubList title="Skill gaps" items={r.red_flags.skill_gaps} />
          <SubList title="Likely challenges" items={r.red_flags.likely_challenges} />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        icon={ListChecks}
        title="Interview checklist"
        count={r.checklist.length}
        defaultOpen
      >
        <ul className="space-y-2">
          {r.checklist.map((item, i) => (
            <li key={i}>
              <label className="flex cursor-pointer items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={checked.has(i)}
                  onChange={() => toggle(i)}
                  className="mt-0.5 h-4 w-4 rounded border-input"
                />
                <span
                  className={cn(
                    checked.has(i) && 'text-muted-foreground line-through',
                  )}
                >
                  {item}
                </span>
              </label>
            </li>
          ))}
        </ul>
      </CollapsibleSection>
    </div>
  );
}
