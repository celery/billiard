import errno
import sys
import tempfile
from unittest.mock import Mock, call, patch

import pytest

from billiard import compat
from billiard.compat import close_open_fds


class test_close_open_fds:

    def test_closes_only_listed_descriptors(self):
        with patch('billiard.compat._open_fds',
                   return_value=[0, 1, 2, 7, 9]), \
                patch('os.close') as close, \
                patch('os.closerange') as closerange:
            close_open_fds([1, 2])
        assert close.call_args_list == [call(0), call(7), call(9)]
        closerange.assert_not_called()

    def test_accepts_file_objects_and_ignores_none(self):
        fh = Mock(name='fh')
        fh.fileno.return_value = 3
        with patch('billiard.compat._open_fds', return_value=[3, 4]), \
                patch('os.close') as close, \
                patch('os.closerange'):
            close_open_fds([None, fh])
        close.assert_called_once_with(4)

    @pytest.mark.parametrize('code', [errno.EBADF, errno.EINTR, errno.EIO])
    def test_ignores_close_errors_like_closerange(self, code):
        exc = OSError()
        exc.errno = code
        with patch('billiard.compat._open_fds', return_value=[5, 6]), \
                patch('os.close', side_effect=exc) as close, \
                patch('os.closerange'):
            close_open_fds()
        assert close.call_args_list == [call(5), call(6)]

    def test_never_calls_get_fdmax_with_fd_dir(self):
        """The limit is irrelevant when the open descriptors can be listed."""
        with patch('billiard.compat._open_fds', return_value=[0, 1, 2]), \
                patch('billiard.compat.get_fdmax') as get_fdmax, \
                patch('os.close'):
            close_open_fds([0, 1, 2])
        get_fdmax.assert_not_called()


class test_close_open_fds_fallback:
    """Without an fd directory the gaps between kept descriptors are closed."""

    def test_closes_ranges_between_kept_descriptors(self):
        with patch('billiard.compat._open_fds', return_value=None), \
                patch('billiard.compat.get_fdmax', return_value=10), \
                patch('os.closerange') as closerange, \
                patch('os.close') as close:
            close_open_fds([1, 2, 5])
        assert closerange.call_args_list == [
            call(0, 1), call(3, 5), call(6, 10),
        ]
        close.assert_not_called()

    def test_accepts_file_objects_and_ignores_none(self):
        fh = Mock(name='fh')
        fh.fileno.return_value = 4
        with patch('billiard.compat._open_fds', return_value=None), \
                patch('billiard.compat.get_fdmax', return_value=6), \
                patch('os.closerange') as closerange, \
                patch('os.close'):
            close_open_fds([None, fh, 4, 0])
        assert closerange.call_args_list == [call(1, 4), call(5, 6)]

    def test_without_keep_closes_whole_range(self):
        with patch('billiard.compat._open_fds', return_value=None), \
                patch('billiard.compat.get_fdmax', return_value=3), \
                patch('os.closerange') as closerange, \
                patch('os.close'):
            close_open_fds()
        closerange.assert_called_once_with(0, 3)

    def test_cost_does_not_grow_with_fdmax(self):
        """One closerange() call per gap, however large the limit is.

        The body before celery/billiard#455 called os.close() once per
        descriptor up to get_fdmax(), which stalls for minutes in containers
        where the limit is ~1e9 (celery/celery#9886).
        """
        with patch('billiard.compat._open_fds', return_value=None), \
                patch('billiard.compat.get_fdmax', return_value=2 ** 20), \
                patch('os.closerange') as closerange, \
                patch('os.close') as close:
            close_open_fds([0, 1, 2])
        closerange.assert_called_once_with(3, 2 ** 20)
        close.assert_not_called()


class test_open_fds:

    def test_fd_dir_matches_this_platform(self):
        if sys.platform == 'darwin':
            assert compat._FD_DIR == '/dev/fd'
        elif sys.platform.startswith(('cygwin', 'freebsd', 'dragonfly')):
            assert compat._FD_DIR == '/dev/fd'
        else:
            assert compat._FD_DIR == '/proc/self/fd'

    @pytest.mark.skipif(sys.platform == 'win32', reason='no fd directory')
    def test_lists_a_descriptor_this_process_opened(self):
        with tempfile.TemporaryFile() as fh:
            fds = compat._open_fds()
            if fds is None:
                pytest.skip(f'fd directory {compat._FD_DIR!r} not available on this system')
            assert fh.fileno() in fds

    def test_returns_none_when_fd_dir_is_missing(self):
        with patch('os.listdir', side_effect=OSError()):
            assert compat._open_fds() is None

    def test_returns_none_on_freebsd_without_fdescfs(self):
        with patch.object(sys, 'platform', 'freebsd14'), \
                patch('billiard.compat._dev_fd_is_fdescfs',
                      return_value=False), \
                patch('os.listdir') as listdir:
            assert compat._open_fds() is None
        listdir.assert_not_called()

    def test_dev_fd_is_fdescfs(self):
        with patch('os.stat', side_effect=[Mock(st_dev=1), Mock(st_dev=2)]):
            assert compat._dev_fd_is_fdescfs()
        with patch('os.stat', side_effect=[Mock(st_dev=1), Mock(st_dev=1)]):
            assert not compat._dev_fd_is_fdescfs()
        with patch('os.stat', side_effect=OSError()):
            assert not compat._dev_fd_is_fdescfs()
