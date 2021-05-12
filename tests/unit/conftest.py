from charm import SplunkCharm

from ops.testing import Harness

import pytest


@pytest.fixture
def harness():
    _harness = Harness(SplunkCharm)
    _harness.set_model_name("testing")
    _harness.begin()
    yield _harness
    _harness.cleanup()
