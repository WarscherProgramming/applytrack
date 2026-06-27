import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.client import AIClient
from app.ai.mock_provider import MockProvider
from app.features.applications.model import ApplicationStatus, JobApplication
from app.features.companies.model import Company
from app.features.interview_ai.model import InterviewPrepPackage
from app.features.job_intelligence.router import _get_service
from app.features.job_intelligence.service import JobIntelligenceService
from app.features.resume_match.model import ResumeMatchAnalysis
from app.features.resumes.service import ResumeService
from app.main import app


def _mock_client(response: str | None = None) -> AIClient:
    payload = response or json.dumps(
        {
            "executive_summary": "Kubernetes and Terraform are the clearest market gaps.",
            "top_learning_priorities": ["Kubernetes", "Terraform"],
            "emerging_technologies": ["Kubernetes"],
            "resume_recommendations": ["Add truthful Kubernetes evidence if available."],
            "skill_investment_suggestions": ["Build a Kubernetes deployment project."],
            "career_direction_suggestions": ["Target backend platform roles."],
            "caveats": [],
        }
    )
    return AIClient(MockProvider(default_response=payload), default_model="mock-model")


def _inject_client(db: Session, client: AIClient | None = None) -> None:
    app.dependency_overrides[_get_service] = lambda: JobIntelligenceService(
        db, ai_client=client or _mock_client()
    )


def _seed_data(db: Session) -> None:
    company = Company(name="Acme Health", industry="Healthcare", location="Remote")
    db.add(company)
    db.flush()
    resume = ResumeService(db).upload(
        file_name="resume.txt",
        content=b"Python backend engineer with Docker and REST API experience.",
        name="Backend Resume",
    )
    application = JobApplication(
        company_id=company.id,
        job_title="Backend Platform Engineer",
        status=ApplicationStatus.INTERVIEW.value,
        resume_id=resume.id,
    )
    db.add(application)
    db.flush()
    db.add(
        ResumeMatchAnalysis(
            resume_id=resume.id,
            resume_name="Backend Resume (v1)",
            job_description=(
                "We need Python, Docker, Kubernetes, Terraform, AWS, FastAPI, "
                "PostgreSQL, microservices, CI/CD, and communication."
            ),
            overall_match_score=78,
            result={"missing_skills": ["Kubernetes", "Terraform"]},
            provider="mock",
            model="mock-model",
        )
    )
    db.add(
        InterviewPrepPackage(
            application_id=application.id,
            resume_id=resume.id,
            company_name=company.name,
            job_title=application.job_title,
            interview_type="technical",
            job_description=(
                "Backend platform role using Python, FastAPI, PostgreSQL, "
                "Kubernetes, AWS, security, testing, and mentoring."
            ),
            result={},
            provider="mock",
            model="mock-model",
        )
    )
    db.flush()


def test_extraction_and_normalization_helpers() -> None:
    service = JobIntelligenceService.__new__(JobIntelligenceService)

    skills = service.extract_skills(
        "Python, C#, React, PostgreSQL, K8s, GitHub Actions, and communication."
    )
    names = {skill.name for skill in skills}

    assert {"Python", "C#", "React", "PostgreSQL", "Kubernetes", "GitHub Actions"} <= names
    assert service.normalize_skill("k8s").name == "Kubernetes"
    assert service.normalize_skill("postgres").name == "PostgreSQL"
    assert service.normalize_skill("not-a-real-skill") is None


def test_report_calculates_market_signals_and_gaps(
    client: TestClient, db: Session
) -> None:
    _seed_data(db)
    _inject_client(db)

    response = client.get("/api/v1/job-intelligence/")

    assert response.status_code == 200
    body = response.json()
    assert body["job_description_count"] == 2
    skill_names = {item["name"] for item in body["skill_signals"]}
    assert {"Python", "Kubernetes", "Terraform", "FastAPI", "PostgreSQL"} <= skill_names
    missing = {item["name"]: item for item in body["missing_skills"]}
    assert "Kubernetes" in missing
    assert missing["Kubernetes"]["resume_match_gap_count"] == 1
    assert "Docker" not in missing
    assert body["industry_breakdown"][0]["name"] in {"Healthcare", "Unknown"}
    assert body["ai_interpretation"]["available"] is True
    assert body["ai_interpretation"]["top_learning_priorities"] == [
        "Kubernetes",
        "Terraform",
    ]


def test_filters_by_industry_and_role(client: TestClient, db: Session) -> None:
    _seed_data(db)
    _inject_client(db)

    healthcare = client.get("/api/v1/job-intelligence/?industry=Healthcare").json()
    finance = client.get("/api/v1/job-intelligence/?industry=Finance").json()
    role = client.get("/api/v1/job-intelligence/?role=Platform").json()

    assert healthcare["job_description_count"] == 1
    assert finance["job_description_count"] == 0
    assert role["job_description_count"] == 1


def test_ai_failure_returns_deterministic_interpretation(
    client: TestClient, db: Session
) -> None:
    _seed_data(db)
    _inject_client(db, _mock_client(response="not json"))

    response = client.get("/api/v1/job-intelligence/")

    assert response.status_code == 200
    body = response.json()
    assert body["ai_interpretation"]["available"] is False
    assert body["missing_skills"]
    assert "AI interpretation unavailable" in body["ai_interpretation"]["caveats"][-1]
