"""Pure email→entity matching with confidence scoring.

Deliberately free of any database, network, or framework code so it can be
unit-tested in isolation. The service loads lightweight context objects from the
DB and hands them here; this module returns a MatchResult of ids + a score.
"""

from dataclasses import dataclass
from uuid import UUID

# Well-known recruiting domains we always recognise, even before the user has
# stored the company in ApplyTrack.
KNOWN_COMPANY_DOMAINS: dict[str, str] = {
    "amazon.com": "Amazon",
    "microsoft.com": "Microsoft",
    "google.com": "Google",
    "meta.com": "Meta",
    "facebook.com": "Meta",
    "apple.com": "Apple",
    "nvidia.com": "NVIDIA",
    "stripe.com": "Stripe",
    "snowflake.com": "Snowflake",
    "datadoghq.com": "Datadog",
    "netflix.com": "Netflix",
    "uber.com": "Uber",
    "lyft.com": "Lyft",
}

# Tokens that signal an email is job-search related.
_RECRUITING_KEYWORDS = (
    "interview",
    "application",
    "recruit",
    "position",
    "role",
    "opportunity",
    "hiring",
    "offer",
    "candidate",
    "onsite",
    "phone screen",
    "assessment",
    "hiring manager",
)


# ---------------------------------------------------------------------------
# Lightweight context objects (plain data; no ORM coupling)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompanyRef:
    id: UUID
    name: str
    domain: str | None = None  # derived from website, if any


@dataclass(frozen=True)
class RecruiterRef:
    id: UUID
    email: str | None
    company_id: UUID | None


@dataclass(frozen=True)
class ApplicationRef:
    id: UUID
    company_id: UUID
    job_title: str


@dataclass(frozen=True)
class InterviewRef:
    id: UUID
    application_id: UUID


@dataclass(frozen=True)
class MatchContext:
    companies: tuple[CompanyRef, ...]
    recruiters: tuple[RecruiterRef, ...]
    applications: tuple[ApplicationRef, ...]
    interviews: tuple[InterviewRef, ...]


@dataclass
class MatchResult:
    company_id: UUID | None = None
    application_id: UUID | None = None
    recruiter_id: UUID | None = None
    interview_id: UUID | None = None
    confidence: float = 0.0
    reason: str | None = None


def extract_domain(email: str | None) -> str | None:
    """'jane@stripe.com' → 'stripe.com'. Returns None if not an address."""
    if not email or "@" not in email:
        return None
    return email.rsplit("@", 1)[1].strip().lower()


def known_company_for_domain(domain: str | None) -> str | None:
    return KNOWN_COMPANY_DOMAINS.get(domain) if domain else None


def is_recruiting_email(
    subject: str | None, body_preview: str | None, sender: str | None
) -> bool:
    """True if the email looks job-related — by keywords or a known sender."""
    domain = extract_domain(sender)
    if known_company_for_domain(domain):
        return True
    haystack = f"{subject or ''} {body_preview or ''}".lower()
    return any(keyword in haystack for keyword in _RECRUITING_KEYWORDS)


def match_email(
    *,
    subject: str | None,
    sender: str | None,
    context: MatchContext,
) -> MatchResult:
    """Link an email to the best entities with a confidence score.

    Strategy, strongest signal first:
      1. Sender == a stored recruiter's email      → recruiter (+ its company)  0.95
      2. Sender domain == a stored company domain   → company                   0.85
      3. Sender domain is a known recruiting domain matching a stored company    0.80
      4. Sender domain is a known recruiting domain (no stored company)          0.60
      5. A stored company name appears in the subject                            0.50
    After a company is chosen, link the (sole or subject-matching) application
    and any interview for it; the result confidence is the company signal,
    nudged up when an application is also linked.
    """
    domain = extract_domain(sender)
    result = MatchResult()

    # 1. Recruiter by exact sender address.
    if sender:
        for recruiter in context.recruiters:
            if recruiter.email and recruiter.email.lower() == sender.lower():
                result.recruiter_id = recruiter.id
                result.company_id = recruiter.company_id
                result.confidence = 0.95
                result.reason = "Recruiter email match"
                break

    # 2 & 3. Company by domain.
    if result.company_id is None and domain:
        for company in context.companies:
            if company.domain and company.domain == domain:
                result.company_id = company.id
                result.confidence = 0.85
                result.reason = "Company domain match"
                break
        if result.company_id is None:
            known = known_company_for_domain(domain)
            if known:
                stored = _find_company_by_name(known, context.companies)
                if stored:
                    result.company_id = stored.id
                    result.confidence = 0.80
                    result.reason = f"Known sender ({known})"
                else:
                    result.confidence = 0.60
                    result.reason = f"Known company ({known})"

    # 5. Company name in subject (only if nothing stronger fired).
    if result.company_id is None and subject:
        lowered = subject.lower()
        for company in context.companies:
            if company.name.lower() in lowered:
                result.company_id = company.id
                result.confidence = max(result.confidence, 0.50)
                result.reason = "Company name in subject"
                break

    # Link an application + interview once we have a company.
    if result.company_id is not None:
        application = _pick_application(
            result.company_id, subject, context.applications
        )
        if application is not None:
            result.application_id = application.id
            result.confidence = min(0.99, result.confidence + 0.05)
            interview = _find_interview(application.id, context.interviews)
            if interview is not None:
                result.interview_id = interview.id

    return result


def _find_company_by_name(
    name: str, companies: tuple[CompanyRef, ...]
) -> CompanyRef | None:
    lowered = name.lower()
    for company in companies:
        if company.name.lower() == lowered:
            return company
    return None


def _pick_application(
    company_id: UUID,
    subject: str | None,
    applications: tuple[ApplicationRef, ...],
) -> ApplicationRef | None:
    candidates = [a for a in applications if a.company_id == company_id]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    # Disambiguate multiple applications by job title appearing in the subject.
    if subject:
        lowered = subject.lower()
        for application in candidates:
            if application.job_title.lower() in lowered:
                return application
    return None  # Ambiguous — link company only, not a specific application.


def _find_interview(
    application_id: UUID, interviews: tuple[InterviewRef, ...]
) -> InterviewRef | None:
    for interview in interviews:
        if interview.application_id == application_id:
            return interview
    return None
