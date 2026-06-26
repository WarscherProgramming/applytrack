from uuid import uuid4

from app.features.gmail.email_matcher import (
    ApplicationRef,
    CompanyRef,
    InterviewRef,
    MatchContext,
    RecruiterRef,
    extract_domain,
    is_recruiting_email,
    known_company_for_domain,
    match_email,
)


def _context(
    *, companies=(), recruiters=(), applications=(), interviews=()
) -> MatchContext:
    return MatchContext(
        companies=tuple(companies),
        recruiters=tuple(recruiters),
        applications=tuple(applications),
        interviews=tuple(interviews),
    )


class TestExtractDomain:
    def test_extracts_domain(self) -> None:
        assert extract_domain("jane@stripe.com") == "stripe.com"

    def test_lowercases(self) -> None:
        assert extract_domain("Jane@Stripe.COM") == "stripe.com"

    def test_returns_none_for_non_address(self) -> None:
        assert extract_domain("not-an-email") is None
        assert extract_domain(None) is None


class TestKnownCompany:
    def test_recognises_known_domains(self) -> None:
        assert known_company_for_domain("amazon.com") == "Amazon"
        assert known_company_for_domain("meta.com") == "Meta"
        assert known_company_for_domain("facebook.com") == "Meta"

    def test_unknown_domain(self) -> None:
        assert known_company_for_domain("example.com") is None


class TestIsRecruitingEmail:
    def test_known_sender_is_recruiting(self) -> None:
        assert is_recruiting_email("Hello", "Just checking in", "careers@amazon.com")

    def test_keyword_in_subject(self) -> None:
        assert is_recruiting_email("Interview scheduled", None, "x@unknown.com")

    def test_keyword_in_body(self) -> None:
        assert is_recruiting_email("Hi", "About the position you applied for", "x@unknown.com")

    def test_non_recruiting(self) -> None:
        assert not is_recruiting_email("Lunch?", "Want to grab food?", "friend@gmail.com")


class TestMatchEmail:
    def test_recruiter_email_is_strongest(self) -> None:
        company_id = uuid4()
        recruiter_id = uuid4()
        ctx = _context(
            recruiters=[RecruiterRef(recruiter_id, "jane@stripe.com", company_id)],
            companies=[CompanyRef(company_id, "Stripe", "stripe.com")],
        )
        result = match_email(subject="Hi", sender="jane@stripe.com", context=ctx)
        assert result.recruiter_id == recruiter_id
        assert result.company_id == company_id
        assert result.confidence >= 0.95

    def test_company_domain_match(self) -> None:
        company_id = uuid4()
        ctx = _context(companies=[CompanyRef(company_id, "Acme", "acme.com")])
        result = match_email(
            subject="Your application", sender="hr@acme.com", context=ctx
        )
        assert result.company_id == company_id
        assert result.confidence >= 0.85

    def test_known_company_without_stored_company(self) -> None:
        ctx = _context()
        result = match_email(
            subject="SDE role", sender="careers@amazon.com", context=ctx
        )
        # Recognised as Amazon but no stored company to link to.
        assert result.company_id is None
        assert result.confidence == 0.60
        assert result.reason and "Amazon" in result.reason

    def test_known_company_links_to_stored(self) -> None:
        company_id = uuid4()
        ctx = _context(companies=[CompanyRef(company_id, "Amazon", None)])
        result = match_email(
            subject="SDE role", sender="careers@amazon.com", context=ctx
        )
        assert result.company_id == company_id
        assert result.confidence >= 0.80

    def test_company_name_in_subject(self) -> None:
        company_id = uuid4()
        ctx = _context(companies=[CompanyRef(company_id, "Globex", None)])
        result = match_email(
            subject="Globex interview invite", sender="x@unknown.com", context=ctx
        )
        assert result.company_id == company_id
        assert result.confidence >= 0.50

    def test_links_sole_application_and_interview(self) -> None:
        company_id = uuid4()
        application_id = uuid4()
        interview_id = uuid4()
        ctx = _context(
            companies=[CompanyRef(company_id, "Acme", "acme.com")],
            applications=[ApplicationRef(application_id, company_id, "Engineer")],
            interviews=[InterviewRef(interview_id, application_id)],
        )
        result = match_email(subject="Update", sender="hr@acme.com", context=ctx)
        assert result.application_id == application_id
        assert result.interview_id == interview_id

    def test_ambiguous_applications_link_company_only(self) -> None:
        company_id = uuid4()
        ctx = _context(
            companies=[CompanyRef(company_id, "Acme", "acme.com")],
            applications=[
                ApplicationRef(uuid4(), company_id, "Backend Engineer"),
                ApplicationRef(uuid4(), company_id, "Frontend Engineer"),
            ],
        )
        result = match_email(subject="Hello", sender="hr@acme.com", context=ctx)
        assert result.company_id == company_id
        assert result.application_id is None

    def test_disambiguates_application_by_subject(self) -> None:
        company_id = uuid4()
        backend_id = uuid4()
        ctx = _context(
            companies=[CompanyRef(company_id, "Acme", "acme.com")],
            applications=[
                ApplicationRef(backend_id, company_id, "Backend Engineer"),
                ApplicationRef(uuid4(), company_id, "Frontend Engineer"),
            ],
        )
        result = match_email(
            subject="Your Backend Engineer application", sender="hr@acme.com", context=ctx
        )
        assert result.application_id == backend_id

    def test_no_match_returns_zero_confidence(self) -> None:
        result = match_email(
            subject="Lunch", sender="friend@gmail.com", context=_context()
        )
        assert result.company_id is None
        assert result.confidence == 0.0
