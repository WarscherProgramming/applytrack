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
import { resumeHooks } from '@/features/resumes/resumes';

import type { InterviewPrepRequest } from '../types';

const MIN_JD = 20;
const NONE = 'none';
const INTERVIEW_TYPES = [
  'Phone Screen',
  'Technical',
  'Behavioral',
  'System Design',
  'Onsite',
  'Hiring Manager',
  'Final',
  'General',
];

interface GenerationFormProps {
  isGenerating: boolean;
  onGenerate: (input: InterviewPrepRequest) => void;
}

export function GenerationForm({ isGenerating, onGenerate }: GenerationFormProps) {
  const { options: resumeOptions } = resumeHooks.useDocumentOptions();
  const { options: applications } = useApplicationOptions();
  const { byId: companyById } = useCompanyOptions();

  const [applicationId, setApplicationId] = useState(NONE);
  const [resumeId, setResumeId] = useState(NONE);
  const [companyName, setCompanyName] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [interviewType, setInterviewType] = useState('General');
  const [interviewRound, setInterviewRound] = useState('');
  const [recruiterNotes, setRecruiterNotes] = useState('');
  const [interviewNotes, setInterviewNotes] = useState('');

  useEffect(() => {
    if (applicationId === NONE) return;
    const app = applications.find((a) => a.id === applicationId);
    if (!app) return;
    setCompanyName(companyById.get(app.company_id) ?? '');
    setJobTitle(app.job_title);
  }, [applicationId, applications, companyById]);

  const hasContext =
    applicationId !== NONE ||
    (companyName.trim().length > 0 && jobTitle.trim().length > 0);
  const canGenerate =
    hasContext && jobDescription.trim().length >= MIN_JD && !isGenerating;

  function handleGenerate() {
    if (!canGenerate) return;
    onGenerate({
      application_id: applicationId === NONE ? null : applicationId,
      resume_id: resumeId === NONE ? null : resumeId,
      company_name: companyName.trim() || null,
      job_title: jobTitle.trim() || null,
      job_description: jobDescription.trim(),
      interview_type: interviewType || null,
      interview_round: interviewRound.trim() || null,
      recruiter_notes: recruiterNotes.trim() || null,
      interview_notes: interviewNotes.trim() || null,
    });
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="ip-application">Application</Label>
        <Select value={applicationId} onValueChange={setApplicationId}>
          <SelectTrigger id="ip-application">
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
          Fills company &amp; title, and uses the application&apos;s submitted
          resume and recent emails if available.
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="ip-resume">Resume (optional)</Label>
        <Select value={resumeId} onValueChange={setResumeId}>
          <SelectTrigger id="ip-resume">
            <SelectValue placeholder="Use application's resume / none" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={NONE}>Use application&apos;s resume / none</SelectItem>
            {resumeOptions.map((opt) => (
              <SelectItem key={opt.id} value={opt.id}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {resumeOptions.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            <Link to="/resumes" className="text-primary hover:underline">
              Upload a resume
            </Link>{' '}
            for STAR coaching grounded in your experience.
          </p>
        ) : null}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="ip-company">Company</Label>
          <Input
            id="ip-company"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            placeholder="e.g. Acme"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="ip-title">Job title</Label>
          <Input
            id="ip-title"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g. Senior Engineer"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="ip-type">Interview type</Label>
          <Select value={interviewType} onValueChange={setInterviewType}>
            <SelectTrigger id="ip-type">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {INTERVIEW_TYPES.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="ip-round">Interview round (optional)</Label>
          <Input
            id="ip-round"
            value={interviewRound}
            onChange={(e) => setInterviewRound(e.target.value)}
            placeholder="e.g. Round 2 of 3"
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="ip-jd">
          Job description <span className="text-destructive">*</span>
        </Label>
        <Textarea
          id="ip-jd"
          rows={7}
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

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="ip-recruiter">Recruiter notes (optional)</Label>
          <Textarea
            id="ip-recruiter"
            rows={3}
            value={recruiterNotes}
            onChange={(e) => setRecruiterNotes(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="ip-inotes">Interview notes (optional)</Label>
          <Textarea
            id="ip-inotes"
            rows={3}
            value={interviewNotes}
            onChange={(e) => setInterviewNotes(e.target.value)}
          />
        </div>
      </div>

      <Button onClick={handleGenerate} disabled={!canGenerate}>
        {isGenerating ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Wand2 className="h-4 w-4" />
        )}
        Generate preparation
      </Button>
    </div>
  );
}
