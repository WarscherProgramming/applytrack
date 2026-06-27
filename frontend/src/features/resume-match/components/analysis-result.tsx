import {
  Copy,
  Download,
  GraduationCap,
  KeyRound,
  Lightbulb,
  ThumbsDown,
  ThumbsUp,
  TriangleAlert,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { formatDateTime } from '@/utils/format';

import {
  analysisToMarkdown,
  downloadTextFile,
  slugify,
} from '../lib';
import type { ResumeMatchAnalysis } from '../types';
import { MatchScore } from './match-score';
import { ResultSection } from './result-section';

interface AnalysisResultProps {
  analysis: ResumeMatchAnalysis;
}

/** Full read-only view of a single analysis with copy/export actions. */
export function AnalysisResult({ analysis }: AnalysisResultProps) {
  const { toast } = useToast();
  const r = analysis.result;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(analysisToMarkdown(analysis));
      toast({ title: 'Copied to clipboard' });
    } catch {
      toast({ variant: 'destructive', title: 'Could not copy to clipboard' });
    }
  }

  function handleExport() {
    const name = `${slugify(analysis.resume_name)}-match.md`;
    downloadTextFile(name, analysisToMarkdown(analysis));
    toast({ title: 'Exported', description: name });
  }

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <CardTitle>Match analysis</CardTitle>
          <p className="text-sm text-muted-foreground">
            {analysis.resume_name} · {formatDateTime(analysis.created_at)}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            <Copy className="h-4 w-4" />
            Copy
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4" />
            Export
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex flex-col items-center gap-4 rounded-lg border bg-muted/30 p-4 sm:flex-row sm:justify-center">
          <MatchScore score={analysis.overall_match_score} />
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <ResultSection
            icon={ThumbsUp}
            iconClassName="text-success"
            title="Strengths"
            items={r.strengths}
          />
          <ResultSection
            icon={ThumbsDown}
            iconClassName="text-destructive"
            title="Weaknesses"
            items={r.weaknesses}
          />
          <ResultSection
            icon={TriangleAlert}
            iconClassName="text-warning"
            title="Missing skills"
            items={r.missing_skills}
          />
          <ResultSection
            icon={KeyRound}
            iconClassName="text-primary"
            title="Recommended keywords"
            items={r.recommended_keywords}
            variant="tags"
          />
        </div>

        <ResultSection
          icon={Lightbulb}
          iconClassName="text-primary"
          title="Recommended resume changes"
          items={r.recommended_resume_changes}
        />
        <ResultSection
          icon={GraduationCap}
          iconClassName="text-primary"
          title="Interview topics"
          items={r.interview_topics}
        />
      </CardContent>
    </Card>
  );
}
