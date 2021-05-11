from ops.testing import Harness
from charm import SplunkCharm
import pytest


@pytest.fixture
def harness():
    _harness = Harness(SplunkCharm)
    _harness.begin()
    yield _harness
