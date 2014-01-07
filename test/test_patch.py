import os
import unittest

from caliendo.patch import patch
from caliendo.patch import patch_lazy

from test.api.myclass import InheritsFooAndBaz, LazyLoadsBar

def run_test_n_times(test, n):
    for i in range(n):
        pid = os.fork()
        if pid:
            os.waitpid(pid, 0)
        else:
            test(i)
            os._exit(0)


class PatchTestCase(unittest.TestCase):

    def test_patch_inherited(self):

        @patch('test.api.myclass.InheritsFooAndBaz.foo', rvalue='bar')
        @patch('test.api.myclass.InheritsFooAndBaz.baz', rvalue='bar')
        def test(i):
            c = InheritsFooAndBaz()
            assert c.foo() == 'bar'
            assert c.baz() == 'bar'

        run_test_n_times(test, 3)

    def test_patch_lazy_loaded_with_rvalue(self):

        @patch_lazy('test.api.myclass.LazyLoadsBar.bar', rvalue='foo')
        def test(i):
            c = LazyLoadsBar()
            assert c.bar() == 'foo'

        run_test_n_times(test, 3)

    def test_patch_lazy_loaded_with_side_effects(self):

        def side_effect(*args, **kwargs):
            assert args[0] == True

        @patch_lazy('test.api.myclass.LazyLoadsBar.bar', side_effect=side_effect)
        def test(i):
            c = LazyLoadsBar()
            c.bar(True)

        run_test_n_times(test, 1)

    def test_patch_lazy_loaded_with_exception(self):

        @patch_lazy('test.api.myclass.LazyLoadsBar.bar', side_effect=Exception('kablooey!'))
        def test(i):
            c = LazyLoadsBar()
            with self.assertRaisesRegexp(Exception, r"kablooey!"):
                c.bar()

        run_test_n_times(test, 3)
