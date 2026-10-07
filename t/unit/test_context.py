import subprocess
import sys


def _get_default_context_attr(platform, attr):
    """Run a subprocess that patches sys.platform before importing billiard.

    This exercises the actual import-time conditional without corrupting
    the module state of the current process.
    """
    result = subprocess.run(
        [sys.executable, '-c',
         'import unittest.mock; '
         f'unittest.mock.patch("sys.platform", {platform!r}).start(); '
         'import billiard.context; '
         f'print(getattr(billiard.context._default_context, {attr!r})())'],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


class test_default_context_darwin:
    """Tests that macOS defaults to spawn, matching CPython (bpo-33725)."""

    def test_default_start_method_is_spawn_on_darwin(self):
        method = _get_default_context_attr('darwin', 'get_start_method')
        assert method == 'spawn'

    def test_default_start_method_is_fork_on_linux(self):
        method = _get_default_context_attr('linux', 'get_start_method')
        assert method == 'fork'

    def test_set_start_method_override_on_darwin(self):
        result = subprocess.run(
            [sys.executable, '-c',
             'import unittest.mock; '
             'unittest.mock.patch("sys.platform", "darwin").start(); '
             'import billiard.context; '
             'ctx = billiard.context._default_context; '
             'assert ctx.get_start_method() == "spawn"; '
             'ctx.set_start_method("fork", force=True); '
             'print(ctx.get_start_method())'],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == 'fork'

    def test_forking_is_enabled_false_on_darwin(self):
        enabled = _get_default_context_attr('darwin', 'forking_is_enabled')
        assert enabled == 'False'

    def test_forking_is_enabled_true_on_linux(self):
        enabled = _get_default_context_attr('linux', 'forking_is_enabled')
        assert enabled == 'True'
