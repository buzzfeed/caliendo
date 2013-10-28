import unittest
import caliendo

from caliendo.patch import patch
from test.foobar import bazbiz

class TestB(unittest.TestCase):

  @patch('test.nested.bazbiz.baz', 'boz')
  @patch('test.nested.bazbiz.biz', 'bit')
  def test_b_1(self):
    assert bazbiz() == 'bozbit' 
    assert caliendo.util.current_test == 'b.test_b_1'

  @patch('test.nested.bazbiz.baz', 'boz')
  @patch('test.nested.bazbiz.biz', 'tar')
  def test_b_2(self):
    assert bazbiz() == 'boztar' 
    assert caliendo.util.current_test == 'b.test_b_2'
     
