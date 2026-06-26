import { z } from 'zod';

/**
 * Validation for the company create/edit form. Mirrors the backend's
 * constraints (name required + max lengths) so users get instant feedback
 * before a request is made. Optional fields use empty-string-to-undefined
 * coercion so blank inputs are omitted rather than sent as "".
 */
const optionalText = (max: number) =>
  z
    .string()
    .trim()
    .max(max, `Must be ${max} characters or fewer`)
    .optional()
    .transform((v) => (v === '' ? undefined : v));

export const companyFormSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'Name is required')
    .max(255, 'Must be 255 characters or fewer'),
  website: optionalText(500),
  industry: optionalText(255),
  location: optionalText(255),
  notes: optionalText(5000),
});

export type CompanyFormValues = z.input<typeof companyFormSchema>;
export type CompanyFormOutput = z.output<typeof companyFormSchema>;
