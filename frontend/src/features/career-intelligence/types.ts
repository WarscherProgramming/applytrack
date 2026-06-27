export interface IntelligenceFilters {
  date_from: string | null;
  date_to: string | null;
  compare_date_from: string | null;
  compare_date_to: string | null;
}

export interface CareerIntelligenceParams {
  date_from?: string;
  date_to?: string;
  compare_date_from?: string;
  compare_date_to?: string;
}

export interface RateMetric {
  value: number | null;
  numerator: number;
  denominator: number;
  label: string;
}

export interface ApplicationMetrics {
  total_applications: number;
  active_applications: number;
  response_rate: RateMetric;
  interview_rate: RateMetric;
  offer_rate: RateMetric;
  offer_acceptance_rate: RateMetric;
  rejection_rate: RateMetric;
  ghost_rate: RateMetric;
  average_days_until_first_response: number | null;
  average_interview_count_per_application: number | null;
}

export interface SegmentInsight {
  name: string;
  total_applications: number;
  responses: number;
  response_rate: number | null;
  average_days_until_first_response: number | null;
}

export interface CompanyInsights {
  most_responsive_companies: SegmentInsight[];
  most_responsive_industries: SegmentInsight[];
  most_responsive_locations: SegmentInsight[];
  fastest_response_companies: SegmentInsight[];
}

export interface DocumentPerformance {
  id: string;
  name: string;
  version: number;
  submitted_applications: number;
  response_rate: number | null;
  interview_rate: number | null;
  offer_rate: number | null;
}

export interface DocumentInsights {
  items: DocumentPerformance[];
  highest_interview_rate: DocumentPerformance | null;
  highest_response_rate: DocumentPerformance | null;
  highest_offer_rate: DocumentPerformance | null;
}

export interface CountInsight {
  name: string;
  count: number;
  percentage: number | null;
}

export interface TrendInsight {
  name: string;
  current_count: number;
  previous_count: number;
  delta: number;
}

export interface SkillIntelligence {
  job_description_count: number;
  most_requested_skills: CountInsight[];
  missing_skills: CountInsight[];
  trending_technologies: TrendInsight[];
  frequently_requested_certifications: CountInsight[];
}

export interface InterviewIntelligence {
  most_common_interview_types: CountInsight[];
  average_interviews_before_offer: number | null;
  common_technical_topics: CountInsight[];
  common_behavioral_themes: CountInsight[];
}

export interface ComparisonMetric {
  name: string;
  current: number | null;
  previous: number | null;
  delta: number | null;
}

export interface PeriodComparison {
  metrics: ComparisonMetric[];
}

export interface AIRecommendation {
  title: string;
  detail: string;
  evidence: string;
}

export interface AIRecommendations {
  available: boolean;
  provider: string | null;
  model: string | null;
  executive_summary: string;
  recommendations: AIRecommendation[];
  caveats: string[];
}

export interface CareerIntelligenceResponse {
  generated_at: string;
  filters: IntelligenceFilters;
  application_metrics: ApplicationMetrics;
  company_insights: CompanyInsights;
  resume_insights: DocumentInsights;
  cover_letter_insights: DocumentInsights;
  skill_intelligence: SkillIntelligence;
  interview_intelligence: InterviewIntelligence;
  ai_recommendations: AIRecommendations;
  comparison: PeriodComparison | null;
}

