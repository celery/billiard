import sys

import pytest

if_win32 = pytest.mark.skipif(
    sys.platform.startswith('win32'),
    reason='Does not work on Windows'
)

unless_win32 = pytest.mark.skipif(
    not sys.platform.startswith('win32'),
    reason='Requires Windows to work'
)
