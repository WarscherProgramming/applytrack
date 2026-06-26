import { z } from 'zod';

/**
 * Validation for the recruiter create/edit form. Mirrors the backend rules:
 * email must be valid if present, and at least one of first name / last name /
 * email is required. Optional text coerces blank → undefined so empty inputs are
 * omitted rather than sent as "".
 */
const optionalText = (max: number) =>
  z
    .string()
    .trim()
    .max(max, `Must be ${max} characters or fewer`)
    .optional()
    .transform((v) => (v === '' ? undefined : v));

export const recruiterFormSchema = z
  .object({
    // 'none' sentinel (Radix Select can't use an empty value); mapped to null
    // in the dialog. company_id is optional.
    company_id: z.string(),
    first_name: optionalText(255),
    last_name: optionalText(255),
    email: z
      .string()
      .trim()
      .optional()
      .refine((v) => !v || z.string().email().safeParse(v).success, {
        message: 'Enter a valid email',
      })
      .transform((v) => (v ? v : undefined)),
    phone: optionalText(50),
    title: optionalText(255),
    linkedin_url: optionalText(2000),
    notes: optionalText(5000),
  })
  // Cross-field rule: a recruiter must be identifiable by name or email.
  .refine((v) => Boolean(v.first_name || v.last_name || v.email), {
    message: 'Provide at least a first name, last name, or email',
    path: ['first_name'],
  });

export type RecruiterFormValues = z.input<typeof recruiterFormSchema>;
export type RecruiterFormOutput = z.output<typeof recruiterFormSchema>;
