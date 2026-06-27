import { Loader2, Wand2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useApplicationOptions } from '@/features/applications/hooks/use-application-options';
import { useCompanyOptions } from '@/features/companies/hooks/use-company-options';
import { coverLetterHooks } from '@/features/cover-letters/cover-letters';
import { resumeHooks } from '@/features/resumes/resumes';

import type { CoverLetterGenerateInput } from '../types';

const MIN_JD = 20;
const NONE = 'none';

interface GenerationFormProps {
  isGenerating: boolean;
  onGenerate: (input: CoverLetterGenerateInput) => void;
}

export function GenerationForm({ isGenerating, onGenerate }: GenerationFormProps) {
  const { options: resumeOptions, isLoading: resumesLoading } =
    resumeHooks.useDocumentOptions();
  const { options: templateOptions } = coverLetterHooks.useDocumentOptions();
  const { options: applications } = useApplicationOptions();
  const { byId: companyById } = useCompanyOptions();

  const [resumeId, setResumeId] = useState('');
  const [applicationId, setApplicationId] = useState<string>(NONE);
  const [companyName, setCompanyName] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [templateId, setTemplateId] = useState<string>(NONE);
  const [jobDescription, setJobDescription] = useState('');
  const [userNotes, setUserNotes] = useState('');

  // When an application is picked, prefill company + title (user can still edit).
  useEffect(() => {
    if (applicationId === NONE) return;
    const app = applications.find((a) => a.id === applicationId);
    if (!app) return;
    setCompanyName(companyById.get(app.company_id) ?? '');
    setJobTitle(app.job_title);
  }, [applicationId, applications, companyById]);

  const noResumes = !resumesLoading && resumeOptions.length === 0;
  const canGenerate =
    Boolean(resumeId) &&
    jobDescription.trim().length >= MIN_JD &&
    companyName.trim().length > 0 &&
    jobTitle.trim().length > 0 &&
    !isGenerating;

  function handleGenerate() {
    if (!canGenerate) return;
    onGenerate({
      resume_id: resumeId,
      job_description: jobDescription.trim(),
      application_id: applicationId === NONE ? null : applicationId,
      company_name: companyName.trim() || null,
      job_title: jobTitle.trim() || null,
      template_cover_letter_id: templateId === NONE ? null : templateId,
      user_notes: userNotes.trim() || null,
    });
  }

  if (noResumes) {
    return (
      <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
        You need a resume first.{' '}
        <Link to="/resumes" className="text-primary hover:underline">
          Upload a resume
        </Link>{' '}
        to generate a cover letter.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="cl-resume">
          Resume <span className="text-destructive">*</span>
        </Label>
        <Select value={resumeId} onValueChange={setResumeId}>
          <SelectTrigger id="cl-resume">
            <SelectValue placeholder="Select a resume" />
          </SelectTrigger>
          <SelectContent>
            {resumeOptions.map((opt) => (
              <SelectItem key={opt.id} value={opt.id}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="cl-application">Application (optional)</Label>
        <Select value={applicationId} onValueChange={setApplicationId}>
          <SelectTrigger id="cl-application">
            <SelectValue placeholder="No application" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={NONE}>No application</SelectItem>
            {applications.map((app) => (
              <SelectItem key={app.id} value={app.id}>
                {app.job_title} — {companyById.get(app.company_id) ?? 'Unknown'}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          Selecting one fills in the company and job title below.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="cl-company">
            Company <span className="text-destructive">*</span>
          </Label>
          <Input
            id="cl-company"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            placeholder="e.g. Acme"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="cl-title">
            Job title <span className="text-destructive">*</span>
          </Label>
          <Input
            id="cl-title"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g. Senior Engineer"
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="cl-template">Existing template (optional)</Label>
        <Select value={templateId} onValueChange={setTemplateId}>
          <SelectTrigger id="cl-template">
            <SelectValue placeholder="No template" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={NONE}>No template</SelectItem>
            {templateOptions.map((opt) => (
              <SelectItem key={opt.id} value={opt.id}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="cl-jd">
          Job description <span className="text-destructive">*</span>
        </Label>
        <Textarea
          id="cl-jd"
          rows={8}
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the job description here…"
          maxLength={20_000}
        />
        <p className="text-xs text-muted-foreground">
          {jobDescription.trim().length < MIN_JD
            ? `At least ${MIN_JD} characters.`
            : `${jobDescription.trim().length.toLocaleString()} characters`}
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="cl-notes">Guidance notes (optional)</Label>
        <Textarea
          id="cl-notes"
          rows={3}
          value={userNotes}
          onChange={(e) => setUserNotes(e.target.value)}
          placeholder="e.g. emphasise leadership, keep it under 300 words"
          maxLength={5_000}
        />
      </div>

      <Button onClick={handleGenerate} disabled={!canGenerate}>
        {isGenerating ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Wand2 className="h-4 w-4" />
        )}
        Generate cover letter
      </Button>
    </div>
  );
}
