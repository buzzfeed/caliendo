import unittest
import time
import random
import os

os.environ['USE_CALIENDO'] = 'True'

from caliendo.db import flatfiles
from caliendo.facade import patch
from caliendo.patch import replay
from caliendo.util import recache
from caliendo import Ignore

import caliendo

from test.api import callback
from test.api.callback import method_calling_method
from test.api.callback import method_with_callback
from test.api.callback import callback_for_method

from test.api.callback import CALLBACK_FILE
from test.api.callback import CACHED_METHOD_FILE

def run_n_times(func, n):
    for i in range(n):
        pid = os.fork()
        if pid:
            os.waitpid(pid, 0)
        else:
            func(i)
            os._exit(0)

class  ReplayTestCase(unittest.TestCase):
    def setUp(self):
        caliendo.util.register_suite()
        recache()
        flatfiles.CACHE_['stacks'] = {}
        flatfiles.CACHE_['seeds'] = {}
        flatfiles.CACHE_['cache'] = {}
        with open(CALLBACK_FILE, 'w+') as f:
            pass
        with open(CACHED_METHOD_FILE, 'w+') as f:
            pass

    def test_replay(self):
        def do_it(i):
            @replay('test.api.callback.callback_for_method')
            @patch('test.api.callback.method_with_callback')
            def test(i):
                cb_file = method_with_callback(callback_for_method, 0.5)
                with open(cb_file, 'rb') as f:
                    contents = f.read()
                    assert contents == ('.' * (i+1)), "Got {0} was expecting {1}".format(contents, ('.' * (i+1)))
            test(i)
            os._exit(0)

        for i in range(2):
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                do_it(i)

        with open(CACHED_METHOD_FILE, 'rb') as f:
            assert f.read() == '.'

    def test_replay_with_ignore(self):
        def do_it(i):
            @replay('test.api.callback.callback_for_method')
            @patch('test.api.callback.method_with_callback', ignore=Ignore([1]))
            def test_(i):
                cb_file = method_with_callback(callback_for_method, random.random())
                with open(cb_file, 'rb') as f:
                    contents = f.read()
                    assert contents == ('.' * (i+1)), "Got {0} was expecting {1}".format(contents, ('.' * (i+1)))
            test_(i)
            os._exit(0)

        for i in range(2):
            pid = os.fork()
            if pid:
                os.waitpid(pid, 0)
            else:
                do_it(i)

        with open(CACHED_METHOD_FILE, 'rb') as f:
            assert f.read() == '.'

if __name__ == '__main__':
    unittest.main()

