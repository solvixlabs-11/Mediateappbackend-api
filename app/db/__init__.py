"""Database module: exports Base and ensures all model registries are loaded."""

# Load all entity models to initialize SQLAlchemy Mapper registry
import app.modules.auth.models  # noqa: F401
import app.modules.common.models  # noqa: F401
import app.modules.files.models  # noqa: F401
import app.modules.users.models  # noqa: F401
from app.db.base import Base

__all__ = ["Base"]
