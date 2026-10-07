"""Compatibility re-export: the implementation lives in ``trusted_provenance_writer``."""

from trusted_provenance_writer import (  # noqa: F401
    ROLE_PREFIX,
    WRITER_ENV,
    WRITER_FUNCTIONS,
    role_exists,
    seed_test_user_instruction,
)
from trusted_provenance_writer import trusted_provenance_writer as trusted_test_writer  # noqa: F401
