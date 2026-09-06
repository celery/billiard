from unittest.mock import Mock, call, patch

from billiard.compat import close_open_fds


class test_close_open_fds:

    def test_closes_ranges_between_kept_descriptors(self):
        with patch('billiard.compat.get_fdmax', return_value=10), \
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
        with patch('billiard.compat.get_fdmax', return_value=6), \
                patch('os.closerange') as closerange, \
                patch('os.close'):
            close_open_fds([None, fh, 4, 0])
        assert closerange.call_args_list == [call(1, 4), call(5, 6)]

    def test_without_keep_closes_whole_range(self):
        with patch('billiard.compat.get_fdmax', return_value=3), \
                patch('os.closerange') as closerange, \
                patch('os.close'):
            close_open_fds()
        closerange.assert_called_once_with(0, 3)

    def test_cost_does_not_grow_with_fdmax(self):
        """One closerange() call per gap, however large the limit is.

        The previous body called os.close() once per descriptor up to
        get_fdmax(), which stalls for minutes in containers where the limit
        is ~1e9 (celery/celery#9886).
        """
        with patch('billiard.compat.get_fdmax', return_value=2 ** 20), \
                patch('os.closerange') as closerange, \
                patch('os.close') as close:
            close_open_fds([0, 1, 2])
        closerange.assert_called_once_with(3, 2 ** 20)
        close.assert_not_called()
