import json

# Offline stand-in used only when the AI platform is in mock mode (no API key),
# so the whole Cover Letter Generator — and the UI — works locally without
# external calls, mirroring the Gmail/Resume Match simulation approach. The
# output is shaped exactly like a real CoverLetterGeneration so it still flows
# through structured parsing and usage tracking; nothing bypasses the provider
# abstraction.


def simulated_cover_letter(company_name: str, job_title: str) -> str:
    """Return a realistic, deterministic CoverLetterGeneration JSON."""
    markdown = (
        f"Dear {company_name} Hiring Team,\n\n"
        f"I am excited to apply for the **{job_title}** role at "
        f"**{company_name}**. My background aligns closely with what your team "
        f"is looking for, and I am eager to contribute.\n\n"
        f"In my previous roles I delivered results directly relevant to this "
        f"position, collaborating across teams to ship reliable, well-tested "
        f"software. I focus on clear communication, pragmatic trade-offs, and "
        f"measurable impact.\n\n"
        f"I would welcome the opportunity to discuss how my experience can help "
        f"{company_name} reach its goals. Thank you for your consideration.\n\n"
        f"Sincerely,\n\n_(Generated offline — configure an AI key for tailored "
        f"output.)_"
    )
    plain_text = (
        f"Dear {company_name} Hiring Team,\n\n"
        f"I am excited to apply for the {job_title} role at {company_name}. "
        f"My background aligns closely with what your team is looking for, and "
        f"I am eager to contribute.\n\n"
        f"In my previous roles I delivered results directly relevant to this "
        f"position, collaborating across teams to ship reliable, well-tested "
        f"software. I focus on clear communication, pragmatic trade-offs, and "
        f"measurable impact.\n\n"
        f"I would welcome the opportunity to discuss how my experience can help "
        f"{company_name} reach its goals. Thank you for your consideration.\n\n"
        f"Sincerely,\n\n(Generated offline — configure an AI key for tailored "
        f"output.)"
    )
    return json.dumps({"markdown": markdown, "plain_text": plain_text})
