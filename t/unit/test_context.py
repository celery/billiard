import importlib

from unittest.mock import patch

import billiard.context


def _reload_context_with_platform(platform):
    """Reload billiard.context with a patched sys.platform.

    Returns the module-level _default_context after re-evaluation.
    """
    with patch('sys.platform', platform):
        importlib.reload(billiard.context)
        return billiard.context._default_context


class test_default_context_darwin:
    """Tests that macOS defaults to spawn, matching CPython (bpo-33725)."""

    def test_default_start_method_is_spawn_on_darwin(self):
        try:
            ctx = _reload_context_with_platform('darwin')
            assert ctx.get_start_method() == 'spawn'
        finally:
            importlib.reload(billiard.context)

    def test_default_start_method_is_fork_on_linux(self):
        try:
            ctx = _reload_context_with_platform('linux')
            assert ctx.get_start_method() == 'fork'
        finally:
            importlib.reload(billiard.context)

    def test_set_start_method_override_on_darwin(self):
        try:
            ctx = _reload_context_with_platform('darwin')
            assert ctx.get_start_method() == 'spawn'
            ctx.set_start_method('fork', force=True)
            assert ctx.get_start_method() == 'fork'
        finally:
            importlib.reload(billiard.context)

    def test_forking_is_enabled_false_on_darwin(self):
        try:
            ctx = _reload_context_with_platform('darwin')
            assert ctx.forking_is_enabled() is False
        finally:
            importlib.reload(billiard.context)

    def test_forking_is_enabled_true_on_linux(self):
        try:
            ctx = _reload_context_with_platform('linux')
            assert ctx.forking_is_enabled() is True
        finally:
            importlib.reload(billiard.context)
