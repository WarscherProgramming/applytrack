from app.shared.base_model import Base  # noqa: F401

# Register every SQLAlchemy model here so Alembic's --autogenerate can diff
# them against the live database schema.
#
# Add one import per feature as models are created:
#   from app.features.<name>.model import <Name>  # noqa: F401

from app.features.companies.model import Company  # noqa: F401
from app.features.applications.model import JobApplication  # noqa: F401
from app.features.recruiters.model import Recruiter  # noqa: F401
from app.features.interviews.model import Interview  # noqa: F401
from app.features.followups.model import FollowUp  # noqa: F401
from app.features.gmail.models import EmailMessage, GmailAccount  # noqa: F401
from app.features.resumes.model import Resume  # noqa: F401
from app.features.cover_letters.model import CoverLetter  # noqa: F401
