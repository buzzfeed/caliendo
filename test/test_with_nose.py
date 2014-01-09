import unittest

from caliendo.patch import patch

class NoseTestCase(unittest.TestCase):

    @patch('test.api.foobar.find')
    def foo(self):
        raise Exception("Should never be run!")

    @patch('test.api.foobar.find')
    def test_foo(self):
        # Should be runnable from cmd as 'nosetests test.test_with_nose:NoseTestCase.test_foo'
        pass
