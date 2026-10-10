import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from sysdesignhelper.content import load_library


@pytest.fixture(scope="session")
def library():
    return load_library()
