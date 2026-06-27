import json

# Offline stand-in used only when the AI platform is in mock mode (no API key),
# so the whole Interview Prep pipeline — and the UI — works locally without
# external calls, mirroring the Resume Match / Cover Letter simulations. Shaped
# exactly like a real InterviewPrepResult so it still flows through structured
# parsing and usage tracking; nothing bypasses the provider abstraction.


def simulated_interview_prep(
    company_name: str, job_title: str, interview_type: str
) -> str:
    payload = {
        "company_overview": {
            "mission": f"{company_name}'s mission, based on the provided details.",
            "products_services": [
                f"{company_name}'s core product line",
                "Supporting services and platforms",
            ],
            "industry": "Derived from the job description and stored data.",
            "culture": "Collaborative, outcome-oriented (inferred from the role).",
            "recent_news": (
                "No external lookup is available — this overview uses only "
                "provided and stored data."
            ),
        },
        "likely_questions": {
            "behavioral": [
                "Tell me about a time you handled a difficult deadline.",
                "Describe a conflict on a team and how you resolved it.",
            ],
            "technical": [
                f"Walk through how you would approach a typical {job_title} problem.",
                "Explain a system you built and the trade-offs you made.",
            ],
            "role_specific": [
                f"What makes you a strong fit for this {job_title} role?",
            ],
            "company_specific": [
                f"Why do you want to work at {company_name}?",
            ],
        },
        "star_examples": [
            {
                "question": "Tell me about a challenging project.",
                "situation": "(Template) Set the context from your resume.",
                "task": "(Template) Describe your specific responsibility.",
                "action": "(Template) Explain the concrete steps you took.",
                "result": "(Template) Quantify the outcome and what you learned.",
            }
        ],
        "study_topics": {
            "languages": ["The role's primary language(s)"],
            "frameworks": ["Frameworks named in the job description"],
            "concepts": ["Core CS concepts relevant to the role"],
            "system_design": ["Designing for scale and reliability"],
            "algorithms": ["Common data structures and complexity analysis"],
            "role_specific": [f"Domain knowledge for a {job_title}"],
        },
        "questions_to_ask": [
            f"How does the team measure success for this {job_title} role?",
            f"What are {company_name}'s biggest priorities this year?",
            "What does the first 90 days look like?",
        ],
        "red_flags": {
            "missing_resume_coverage": [
                "Areas in the job description not evidenced in the resume."
            ],
            "skill_gaps": ["Skills to brush up before the interview."],
            "likely_challenges": [
                f"Expect probing on areas central to a {interview_type} interview."
            ],
        },
        "checklist": [
            f"Research {company_name}'s products and recent direction",
            "Prepare a portfolio / work samples",
            "Re-read your resume and rehearse key stories",
            "Prepare thoughtful questions for the interviewer",
            "Confirm logistics: time, location/link, and contacts",
        ],
    }
    return json.dumps(payload)
