import { z } from 'zod';

import { APPLICATION_STATUSES } from '../constants';

/**
 * Validation for the application create/edit form. Mirrors the backend's
 * constraints so users get instant feedback. Optional text fields coerce blank
 * strings to undefined so empty inputs are omitted rather than sent as "".
 */
const optionalText = (max: number) =>
  z
    .string()
    .trim()
    .max(max, `Must be ${max} characters or fewer`)
    .optional()
    .transform((v) => (v === '' ? undefined : v));

// A select whose "none" sentinel (and empty string) become null — an explicit
// "clear this reference" on submit. Otherwise the chosen id passes through.
const NONE = 'none';
const optionalRef = z
  .string()
  .optional()
  .transform((v) => (!v || v === NONE ? null : v));

export const applicationFormSchema = z.object({
  company_id: z.string().min(1, 'Company is required'),
  job_title: z
    .string()
    .trim()
    .min(1, 'Job title is required')
    .max(255, 'Must be 255 characters or fewer'),
  job_link: optionalText(2000),
  location: optionalText(255),
  salary_range: optionalText(255),
  status: z.enum(APPLICATION_STATUSES),
  // HTML date input yields 'YYYY-MM-DD'; blank → undefined (field omitted).
  date_applied: z
    .string()
    .optional()
    .transform((v) => (v === '' ? undefined : v)),
  source: optionalText(255),
  notes: optionalText(5000),
  resume_id: optionalRef,
  cover_letter_id: optionalRef,
});

export const NONE_DOCUMENT = NONE;

export type ApplicationFormValues = z.input<typeof applicationFormSchema>;
export type ApplicationFormOutput = z.output<typeof applicationFormSchema>;
