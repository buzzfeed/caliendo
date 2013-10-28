import sys
import unittest
import caliendo
from caliendo.patch import patch
from test.foobar import bazbiz 

class TestA(unittest.TestCase):
  
  @patch('test.nested.bazbiz.baz', 'biz')
  @patch('test.nested.bazbiz.biz', 'bat')
  def test_a_1(self):
    assert bazbiz() == 'bizbat' 
    assert caliendo.util.current_test == 'a.test_a_1'

  @patch('test.nested.bazbiz.baz', 'biz')
  @patch('test.nested.bazbiz.biz', 'bat')
  def test_a_2(self):
    assert bazbiz() == 'bizbat' 
    assert caliendo.util.current_test == 'a.test_a_2'
     
