from app.shared.base_model import Base  # noqa: F401

# Register every SQLAlchemy model here so Alembic's --autogenerate can diff
# them against the live database schema.
#
# Add one import per feature as models are created:
#   from app.features.<name>.model import <Name>  # noqa: F401

from app.features.companies.model import Company  # noqa: F401
from app.features.applications.model import JobApplication  # noqa: F401
