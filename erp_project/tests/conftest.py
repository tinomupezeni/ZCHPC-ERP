"""
Test-specific configuration and fixtures.

Inherits from root conftest.py.
Add test-specific fixtures here.
"""

import pytest


# =============================================================================
# Shared Kernel Test Fixtures
# =============================================================================

@pytest.fixture
def sample_money():
    """Create sample Money value objects for testing."""
    # Will be implemented when Money class is created
    pass


@pytest.fixture
def sample_period():
    """Create sample Period value objects for testing."""
    # Will be implemented when Period class is created
    pass


# =============================================================================
# Module-Specific Fixture Imports
# =============================================================================

# These will be added as modules are implemented:
# from tests.unit.modules.hr.conftest import *
# from tests.unit.modules.payroll.conftest import *
