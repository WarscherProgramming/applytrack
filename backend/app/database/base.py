# Register every SQLAlchemy model here so Alembic's --autogenerate can diff
# them against the live database schema.
#
# Add one import per feature as models are created:
#   from app.features.<name>.model import <Name>  # noqa: F401
from app.ai.usage_tracker import AIUsageRecord  # noqa: F401
from app.features.applications.model import JobApplication  # noqa: F401
from app.features.auth.model import RefreshToken  # noqa: F401
from app.features.calendar_integration.model import (  # noqa: F401
    CalendarConnection,
    CalendarSyncEvent,
)
from app.features.companies.model import Company  # noqa: F401
from app.features.cover_letters.model import CoverLetter  # noqa: F401
from app.features.daily_briefing.model import Notification  # noqa: F401
from app.features.followups.model import FollowUp  # noqa: F401
from app.features.gmail.models import EmailMessage, GmailAccount  # noqa: F401
from app.features.interview_ai.model import InterviewPrepPackage  # noqa: F401
from app.features.interviews.model import Interview  # noqa: F401
from app.features.recruiters.model import Recruiter  # noqa: F401
from app.features.resume_match.model import ResumeMatchAnalysis  # noqa: F401
from app.features.resumes.model import Resume  # noqa: F401
from app.features.settings.model import UserSettings  # noqa: F401
from app.features.tasks.model import Task  # noqa: F401
from app.features.users.model import User  # noqa: F401
from app.shared.base_model import Base  # noqa: F401
