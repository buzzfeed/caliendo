from nested.bazbiz import baz, biz

def foo():
    return 'foo'

def bar():
    return 'bar'

def bazbiz():
    return baz() + biz()
