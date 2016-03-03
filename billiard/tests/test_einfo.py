try:
    import cPickle
except ImportError:
    cPickle = None
import pickle
import sys
import traceback

from mock import patch

from ..einfo import ExceptionInfo
from .utils import Case

PY3 = sys.version_info[0] == 3

def with_outer_frames(cb):
    def outer_1():
        return outer_2()

    def outer_2():
        return outer_3()

    def outer_3():
        return cb()

    return outer_1


def make_einfo(exc):
    """
    Make an ExceptionInfo with some "inner" frames we'll do assertions on.
    """
    def inner_1():
        return inner_2()

    def inner_2():
        return inner_3()

    def inner_3():
        raise exc

    try:
        inner_1()
    except:
        return ExceptionInfo()


class TestExceptionInfo(Case):

    def test_raise(self):
        ei = make_einfo(RuntimeError('booom!'))
        try:
            ei.raise_()
        except Exception:
            err = traceback.format_exc()
            self.assertIn('inner_1', err)
            self.assertIn('inner_2', err)
            self.assertIn('inner_3', err)
            if PY3:
                self.assertIn('The above exception was the direct cause of the following exception', err)
        else:
            self.fail("ei.raise_() didn't raise exception !")

    def test_raise_with_outer_frames(self, ei=None):
        ei = ei or make_einfo(RuntimeError('booom!'))
        try:
            with_outer_frames(ei.raise_)()
        except Exception:
            err = traceback.format_exc()
            self.assertIn('inner_1', err)
            self.assertIn('inner_2', err)
            self.assertIn('inner_3', err)
            self.assertIn('outer_1', err)
            self.assertIn('outer_2', err)
            self.assertIn('outer_3', err)
            if PY3:
                self.assertIn('The above exception was the direct cause of the following exception', err)
        else:
            self.fail("ei.raise_() didn't raise exception !")

    def test_raise_unsupported(self, ei=None):
        ei = ei or make_einfo(RuntimeError('booom!'))
        with patch('billiard.einfo._tb_set_next', None):
            with patch('billiard.einfo._tproxy', None):
                self.assertEqual(ei.tb.as_traceback(), None)
                try:
                    with_outer_frames(ei.raise_)()
                except Exception:
                    err = traceback.format_exc()
                    self.assertNotIn('inner_1', err)
                    self.assertNotIn('inner_2', err)
                    self.assertNotIn('inner_3', err)
                    self.assertIn('outer_1', err)
                    self.assertIn('outer_2', err)
                    self.assertIn('outer_3', err)
                    if PY3:
                        self.assertIn('The above exception was the direct cause of the following exception', err)
                else:
                    self.fail("ei.raise_() didn't raise exception !")

    def test_pickle(self):
        ei = make_einfo(RuntimeError('booom!'))
        return pickle.dumps(ei)

    def test_unpickle(self):
        ei = pickle.loads(self.test_pickle())
        self.test_raise_unsupported(ei)

    def test_unpickle_unsupported(self):
        ei = pickle.loads(self.test_pickle())
        self.test_raise_with_outer_frames(ei)

    if cPickle:
        def test_cpickle(self):
            ei = make_einfo(RuntimeError('booom!'))
            return cPickle.dumps(ei)

        def test_uncpickle(self):
            ei = cPickle.loads(self.test_pickle())
            self.test_raise_with_outer_frames(ei)

        def test_uncpickle_unsupported(self):
            ei = cPickle.loads(self.test_pickle())
            self.test_raise_unsupported(ei)

