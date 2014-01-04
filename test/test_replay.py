import unittest
import random
import os

os.environ['USE_CALIENDO'] = 'True'

from caliendo.db.flatfiles import STACK_DIRECTORY
from caliendo.facade import patch
from caliendo.patch import replay
from caliendo.util import recache
from caliendo import Ignore

import caliendo

from api import foobar
from api.foobar import method_calling_method
from api.foobar import method_with_callback
from api.foobar import callback_for_method

class  ReplayTestCase(unittest.TestCase):
    def setUp(self):
        caliendo.util.register_suite()
        stackfiles = os.listdir(STACK_DIRECTORY)
        for f in stackfiles:
            filepath = os.path.join(STACK_DIRECTORY, f)
            if os.path.exists(filepath):
                os.unlink(filepath)
        recache()

    def test_replay(self):
        def run_test(i):
            @replay('test.api.foobar.callback_for_method')
            @patch('test.api.foobar.method_with_callback')
            def test(i):
                filename = method_with_callback(callback_for_method)
                with open(filename, 'rb') as f:
                    assert f.read() == ('.' * (i+1))

            test(i)
            os._exit(0)


        for i in range(3):
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                run_test(i)

        with open(foobar.file.name, 'rb') as f:
            assert f.read() == '.'

        filename = method_calling_method()
        if os.path.exists(filename):
            os.unlink(filename)
        if os.path.exists(foobar.file.name):
            os.unlink(foobar.file.name)

    def test_replay_with_ignore(self):
        def run_test(i):
            @replay('test.api.foobar.callback_for_method')
            @patch('test.api.foobar.method_with_callback', ignore=Ignore(args=[1]))
            def test(i):
                filename = method_with_callback(callback_for_method, random.random())
                with open(filename, 'rb') as f:
                    assert f.read() == ('.' * (i+1))

            test(i)
            os._exit(0)


        for i in range(3):
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                run_test(i)

        with open(foobar.file.name, 'rb') as f:
            assert f.read() == '.'

        filename = method_calling_method()
        if os.path.exists(filename):
            os.unlink(filename)
        if os.path.exists(foobar.file.name):
            os.unlink(foobar.file.name)

        

if __name__ == '__main__':
    unittest.main()

