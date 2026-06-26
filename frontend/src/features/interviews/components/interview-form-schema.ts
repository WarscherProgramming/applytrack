import { z } from 'zod';

import { INTERVIEW_STATUSES } from '../constants';

/**
 * Validation for the interview create/edit form. Mirrors the backend:
 * application + scheduled time required, duration 15–480 minutes, everything
 * else optional. Optional text coerces blank → undefined.
 */
const optionalText = (max: number) =>
  z
    .string()
    .trim()
    .max(max, `Must be ${max} characters or fewer`)
    .optional()
    .transform((v) => (v === '' ? undefined : v));

export const interviewFormSchema = z.object({
  application_id: z.string().min(1, 'Application is required'),
  // 'none' sentinels mapped to null in the dialog (Radix Select needs values).
  recruiter_id: z.string(),
  interview_type: z.string(),
  // datetime-local string ('YYYY-MM-DDTHH:mm'); converted to ISO on submit.
  scheduled_at: z.string().min(1, 'Date and time are required'),
  duration_minutes: z.coerce
    .number({ message: 'Enter a number' })
    .int('Whole minutes only')
    .min(15, 'Minimum 15 minutes')
    .max(480, 'Maximum 480 minutes'),
  location: optionalText(255),
  meeting_link: optionalText(2000),
  status: z.enum(INTERVIEW_STATUSES),
  notes: optionalText(5000),
  feedback: optionalText(5000),
});

export type InterviewFormValues = z.input<typeof interviewFormSchema>;
export type InterviewFormOutput = z.output<typeof interviewFormSchema>;
