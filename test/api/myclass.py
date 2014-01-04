import os

side_effect = 0

class MyClass:
  def foo(self, bar=1):
    global side_effect
    side_effect += 1
    return 'foo'

  def baz(self, bar=1):
    global side_effect
    side_effect += 1
    return os.urandom(1024 * 1024)

class InheritsFooAndBaz(MyClass):
    pass

class LazyLoadsBar(object):
    def __getattr__(self, key):
        if key == 'bar':
            return lambda *args, **kwargs: 'bar'
