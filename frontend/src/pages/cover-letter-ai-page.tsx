import { Sparkles } from 'lucide-react';
import { useState } from 'react';

import { PageHeader } from '@/components/common/page-header';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { CoverLetterOutput } from '@/features/cover-letter-ai/components/cover-letter-output';
import { GeneratingIndicator } from '@/features/cover-letter-ai/components/generating-indicator';
import { GenerationForm } from '@/features/cover-letter-ai/components/generation-form';
import { GenerationHistory } from '@/features/cover-letter-ai/components/generation-history';
import { useGenerateCoverLetter } from '@/features/cover-letter-ai/hooks';
import type {
  CoverLetterGenerateInput,
  GenerationHistoryEntry,
} from '@/features/cover-letter-ai/types';
import { getErrorMessage } from '@/lib/errors';
import { useToast } from '@/hooks/use-toast';

export function CoverLetterAIPage() {
  const { toast } = useToast();
  const generate = useGenerateCoverLetter();

  const [generations, setGenerations] = useState<GenerationHistoryEntry[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [lastInput, setLastInput] = useState<CoverLetterGenerateInput | null>(null);

  function run(input: CoverLetterGenerateInput) {
    setLastInput(input);
    generate.mutate(input, {
      onSuccess: (response) => {
        const entry: GenerationHistoryEntry = {
          id: crypto.randomUUID(),
          createdAt: Date.now(),
          ...response,
        };
        setGenerations((prev) => [entry, ...prev]);
        setSelectedId(entry.id);
      },
      onError: (error) =>
        toast({
          variant: 'destructive',
          title: 'Could not generate cover letter',
          description: getErrorMessage(error),
        }),
    });
  }

  const current = generations.find((g) => g.id === selectedId) ?? null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Cover Letter"
        description="Generate a tailored cover letter from a resume and job description."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Generate</CardTitle>
              <CardDescription>
                Pick a resume and provide the role details. Nothing is saved
                until you choose to save a version.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <GenerationForm isGenerating={generate.isPending} onGenerate={run} />
            </CardContent>
          </Card>

          {generate.isPending ? (
            <GeneratingIndicator />
          ) : current ? (
            <CoverLetterOutput
              key={current.id}
              generation={current}
              isRegenerating={generate.isPending}
              onRegenerate={() => lastInput && run(lastInput)}
            />
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-base font-semibold">No cover letter yet</h3>
                  <p className="mx-auto max-w-sm text-sm text-muted-foreground">
                    Fill in the form and generate a tailored cover letter.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>This session</CardTitle>
              <CardDescription>Generated letters — click to reopen.</CardDescription>
            </CardHeader>
            <CardContent>
              <GenerationHistory
                entries={generations}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
