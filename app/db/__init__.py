"""Database module: exports Base and ensures all model registries are loaded."""

import app.modules.approvals.models  # noqa: F401
import app.modules.attendance.models  # noqa: F401
import app.modules.auth.models  # noqa: F401
import app.modules.common.models  # noqa: F401
import app.modules.customers.models  # noqa: F401
import app.modules.dcr.models  # noqa: F401
import app.modules.expenses.models  # noqa: F401
import app.modules.files.models  # noqa: F401
import app.modules.leaves.models  # noqa: F401
import app.modules.masters.models  # noqa: F401
import app.modules.territories.models  # noqa: F401
import app.modules.tours.models  # noqa: F401
import app.modules.users.models  # noqa: F401
from app.db.base import Base

__all__ = ["Base"]
