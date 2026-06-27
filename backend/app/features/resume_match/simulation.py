import json

# Deterministic, offline stand-in for a real model response. Used only when the
# AI platform is in mock mode (no API key) so the whole Resume Match pipeline —
# and the UI — works locally without external calls, mirroring the Gmail
# integration's simulation mode. The output is intentionally shaped exactly like
# a real ResumeMatchResult so it still flows through structured parsing and usage
# tracking; nothing in the feature bypasses the provider abstraction.


def simulated_match_response(prompt: str) -> str:
    """Return a realistic, deterministic ResumeMatchResult JSON for `prompt`.

    The score is derived from the prompt length so different resume/JD pairs
    produce different (but stable) scores in local development.
    """
    score = 68 + (len(prompt) % 28)  # 68–95, deterministic per input
    payload = {
        "overall_match_score": score,
        "strengths": [
            "Relevant hands-on experience for the core responsibilities",
            "Solid foundation in the primary technologies the role requires",
        ],
        "weaknesses": [
            "Limited evidence of leadership or ownership at scale",
            "Few quantified achievements (impact, metrics)",
        ],
        "missing_skills": [
            "A required tool or framework not mentioned in the resume",
            "Domain-specific experience called out in the job description",
        ],
        "recommended_keywords": [
            "the role's primary stack",
            "key methodologies named in the posting",
        ],
        "recommended_resume_changes": [
            "Quantify accomplishments with concrete metrics",
            "Mirror the job description's terminology in your summary",
            "Lead each bullet with a strong action verb and an outcome",
        ],
        "interview_topics": [
            "System design relevant to the team's domain",
            "Trade-offs in your most significant project",
            "How you handle ambiguity and shifting priorities",
        ],
    }
    return json.dumps(payload)
