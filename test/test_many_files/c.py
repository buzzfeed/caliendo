import unittest
import caliendo

from caliendo.patch import patch
from test.foobar import bazbiz

class TestC(unittest.TestCase):

  @patch('test.nested.bazbiz.biz', 'bat')
  @patch('test.nested.bazbiz.baz', 'buz')
  def test_c_1(self):
    assert bazbiz() == 'buzbat' 
    assert caliendo.util.current_test == 'c.test_c_1'

  @patch('test.nested.bazbiz.baz', 'buz')
  @patch('test.nested.bazbiz.biz', 'but')
  def test_c_2(self):
    assert bazbiz() == 'buzbut' 
    assert caliendo.util.current_test == 'c.test_c_2'
     
