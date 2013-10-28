from test.api.services.foo import find as find_foo
from test.api.services.biz import find as find_biz

def find(how_many):
    return zip(find_foo(how_many), find_biz(how_many))